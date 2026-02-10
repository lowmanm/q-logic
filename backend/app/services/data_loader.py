"""Data Loader: streams CSV rows into a provisioned dynamic table in batches."""

import csv
import io
from datetime import datetime

from dateutil import parser as dateutil_parser
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.registry import SourceMetadata, ColumnMetadata

BATCH_SIZE = 500

# Conversion functions keyed by the data type stored in column_metadata.
# Each returns a Python value suitable for asyncpg parameterized queries.


def _to_text(value: str) -> str:
    return value


def _to_integer(value: str) -> int | None:
    try:
        return int(value.strip().replace(",", ""))
    except (ValueError, AttributeError):
        return None


def _to_float(value: str) -> float | None:
    try:
        return float(value.strip().replace(",", ""))
    except (ValueError, AttributeError):
        return None


def _to_boolean(value: str) -> bool | None:
    v = value.strip().lower()
    if v in ("true", "yes", "1", "t", "y"):
        return True
    if v in ("false", "no", "0", "f", "n"):
        return False
    return None


def _to_timestamp(value: str) -> datetime | None:
    try:
        return dateutil_parser.parse(value.strip(), fuzzy=False)
    except (ValueError, OverflowError):
        return None


_CONVERTERS = {
    "STRING": _to_text,
    "INTEGER": _to_integer,
    "FLOAT": _to_float,
    "BOOLEAN": _to_boolean,
    "DATE": _to_timestamp,
}


class LoadResult:
    __slots__ = ("rows_loaded", "rows_failed", "errors")

    def __init__(self) -> None:
        self.rows_loaded: int = 0
        self.rows_failed: int = 0
        self.errors: list[str] = []

    def record_error(self, row_num: int, col: str, raw: str, reason: str) -> None:
        if len(self.errors) < 50:  # cap error list to prevent memory bloat
            self.errors.append(f"Row {row_num}, column '{col}': {reason} (value: {raw!r})")
        self.rows_failed += 1


def _build_column_map(
    source: SourceMetadata,
) -> list[tuple[str, str, str]]:
    """Return list of (csv_header, physical_name, data_type) from registry."""
    # The column_metadata stores original_name → physical_name mapping implicitly:
    # physical_name was derived from original_name at provisioning time.
    # We need the display_name for error messages but route by physical_name.
    result = []
    for col in source.columns:
        # We use physical_name as both the target column and the CSV-match key.
        # However, the CSV header is the *original* column name.  The original
        # name was sanitised to produce physical_name, so we need to match
        # CSV headers to physical names.  We'll build a reverse lookup in the
        # caller.
        result.append((col.physical_name, col.physical_name, col.data_type))
    return result


async def load_csv(
    db: AsyncSession,
    source: SourceMetadata,
    file_content: bytes,
) -> LoadResult:
    """
    Parse *all* rows of a CSV and insert them into the dynamic table.

    Uses batched INSERT for throughput on large files.  Type conversion
    errors are captured per-row and reported; valid rows still load.
    """
    result = LoadResult()

    # Ensure columns are loaded
    if not source.columns:
        from sqlalchemy import select

        stmt = (
            select(SourceMetadata)
            .options(selectinload(SourceMetadata.columns))
            .where(SourceMetadata.id == source.id)
        )
        res = await db.execute(stmt)
        source = res.scalar_one()

    # Build mapping: csv original_name -> (physical_name, converter)
    # physical_name was derived from original_name via _sanitize_identifier
    # in provisioning.  We need to match CSV headers to column_metadata.
    # Strategy: build a lookup from a sanitised version of the CSV header.
    import re

    def _sanitize(name: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
        return slug[:63]

    col_lookup: dict[str, tuple[str, callable]] = {}
    for col_meta in source.columns:
        converter = _CONVERTERS.get(col_meta.data_type, _to_text)
        col_lookup[col_meta.physical_name] = (col_meta.physical_name, converter)

    # Parse CSV
    text_content = file_content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text_content))
    csv_headers = reader.fieldnames or []

    # Map each CSV header to its physical column
    header_to_physical: dict[str, tuple[str, callable]] = {}
    for hdr in csv_headers:
        sanitized = _sanitize(hdr)
        if sanitized in col_lookup:
            header_to_physical[hdr] = col_lookup[sanitized]

    if not header_to_physical:
        result.errors.append("No CSV columns matched the provisioned schema.")
        return result

    # Ordered list for consistent INSERT column order
    physical_names = [phys for phys, _ in header_to_physical.values()]
    csv_keys = list(header_to_physical.keys())
    converters = [header_to_physical[k][1] for k in csv_keys]

    table_name = source.table_name
    placeholders = ", ".join(f":p{i}" for i in range(len(physical_names)))
    col_list = ", ".join(f'"{p}"' for p in physical_names)
    insert_sql = f'INSERT INTO "{table_name}" ({col_list}) VALUES ({placeholders})'

    batch: list[dict] = []
    row_num = 0

    for row in reader:
        row_num += 1
        params: dict = {}
        row_ok = True

        for i, csv_key in enumerate(csv_keys):
            raw = (row.get(csv_key) or "").strip()
            if not raw:
                params[f"p{i}"] = None
                continue
            converted = converters[i](raw)
            if converted is None and raw:
                # Conversion failed on a non-empty value
                result.record_error(
                    row_num,
                    csv_key,
                    raw,
                    f"Cannot convert to {source.columns[i].data_type}",
                )
                row_ok = False
                break
            params[f"p{i}"] = converted

        if not row_ok:
            continue

        batch.append(params)

        if len(batch) >= BATCH_SIZE:
            await _flush_batch(db, insert_sql, batch)
            result.rows_loaded += len(batch)
            batch = []

    # Flush remaining rows
    if batch:
        await _flush_batch(db, insert_sql, batch)
        result.rows_loaded += len(batch)

    await db.commit()
    return result


async def _flush_batch(
    db: AsyncSession, insert_sql: str, batch: list[dict]
) -> None:
    """Execute a batch of INSERT statements."""
    stmt = text(insert_sql)
    for params in batch:
        await db.execute(stmt, params)
