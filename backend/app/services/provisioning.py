"""Dynamic Table Provisioning: creates PostgreSQL tables from finalized schemas."""

import re
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.registry import SourceMetadata, ColumnMetadata
from app.schemas.schema_inference import FinalizedColumn

# Whitelist of allowed SQL types to prevent injection via type field
_TYPE_MAP = {
    "STRING": "TEXT",
    "INTEGER": "BIGINT",
    "FLOAT": "DOUBLE PRECISION",
    "BOOLEAN": "BOOLEAN",
    "DATE": "TIMESTAMP",
}

# Pattern for valid SQL identifiers (letters, digits, underscores; must start with letter)
_VALID_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]*$")


def _sanitize_identifier(name: str) -> str:
    """Convert a name to a safe SQL identifier. Raises ValueError on failure."""
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    if not slug or not _VALID_IDENTIFIER.match(slug):
        raise ValueError(f"Cannot create safe SQL identifier from: {name!r}")
    return slug[:63]  # PostgreSQL identifier limit


def _make_table_name(project_name: str) -> str:
    return "src_" + _sanitize_identifier(project_name)


async def provision_table(
    db: AsyncSession,
    project_name: str,
    columns: list[FinalizedColumn],
    screen_pop_url_template: str | None = None,
) -> SourceMetadata:
    """
    Create a new PostgreSQL table for the given project and register it.

    Steps:
    1. Validate all identifiers and types.
    2. Execute CREATE TABLE DDL.
    3. Insert registry rows into source_metadata and column_metadata.
    """
    table_name = _make_table_name(project_name)

    # Build column definitions
    col_defs: list[str] = ['"id" BIGSERIAL PRIMARY KEY']
    physical_names: list[str] = []

    for col in columns:
        phys_name = _sanitize_identifier(col.original_name)
        sql_type = _TYPE_MAP.get(col.data_type.upper())
        if sql_type is None:
            raise ValueError(
                f"Unsupported data type: {col.data_type}. "
                f"Allowed: {', '.join(_TYPE_MAP.keys())}"
            )
        physical_names.append(phys_name)
        col_defs.append(f'"{phys_name}" {sql_type}')

    ddl = f'CREATE TABLE "{table_name}" (\n  ' + ",\n  ".join(col_defs) + "\n);"

    # Execute DDL
    await db.execute(text(ddl))

    # Register in source_metadata
    source = SourceMetadata(
        project_name=project_name,
        table_name=table_name,
        screen_pop_url_template=screen_pop_url_template,
    )
    db.add(source)
    await db.flush()  # get source.id

    # Register column metadata
    for col, phys_name in zip(columns, physical_names):
        col_meta = ColumnMetadata(
            source_id=source.id,
            physical_name=phys_name,
            display_name=col.display_name,
            data_type=col.data_type.upper(),
            is_unique_id=col.is_unique_id,
        )
        db.add(col_meta)

    await db.commit()
    await db.refresh(source, attribute_names=["columns"])
    return source
