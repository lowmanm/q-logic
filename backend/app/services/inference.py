"""Schema Inference Engine: reads CSV and detects column data types."""

import csv
import io
import re
from datetime import datetime

from dateutil import parser as dateutil_parser

from app.schemas.schema_inference import InferredColumn

# Allowed inferred types
TYPE_STRING = "STRING"
TYPE_INTEGER = "INTEGER"
TYPE_FLOAT = "FLOAT"
TYPE_BOOLEAN = "BOOLEAN"
TYPE_DATE = "DATE"

_BOOL_TRUE = {"true", "yes", "1", "t", "y"}
_BOOL_FALSE = {"false", "no", "0", "f", "n"}


def _is_boolean(value: str) -> bool:
    return value.strip().lower() in _BOOL_TRUE | _BOOL_FALSE


def _is_integer(value: str) -> bool:
    try:
        int(value.strip().replace(",", ""))
        return True
    except ValueError:
        return False


def _is_float(value: str) -> bool:
    try:
        float(value.strip().replace(",", ""))
        return True
    except ValueError:
        return False


def _is_date(value: str) -> bool:
    try:
        dateutil_parser.parse(value.strip(), fuzzy=False)
        return True
    except (ValueError, OverflowError):
        return False


def _infer_type(values: list[str]) -> str:
    """Infer the best data type from a sample of non-empty values."""
    if not values:
        return TYPE_STRING

    # Check boolean first (most restrictive pattern)
    if all(_is_boolean(v) for v in values):
        return TYPE_BOOLEAN

    # Check integer
    if all(_is_integer(v) for v in values):
        return TYPE_INTEGER

    # Check float
    if all(_is_float(v) for v in values):
        return TYPE_FLOAT

    # Check date — require at least 60% to parse as dates
    date_count = sum(1 for v in values if _is_date(v))
    if date_count / len(values) >= 0.6:
        return TYPE_DATE

    return TYPE_STRING


def _slugify(name: str) -> str:
    """Convert a header name to a human-friendly display name."""
    # Replace underscores and hyphens with spaces
    name = re.sub(r"[_\-]+", " ", name)
    # Insert space before uppercase letters in camelCase
    name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
    return name.strip().title()


def _is_primary_key_candidate(col_name: str, values: list[str]) -> bool:
    """Heuristic: column is a PK candidate if all values are unique and non-empty."""
    lower = col_name.lower()
    name_hints = ("id", "key", "code", "number", "num", "no")
    has_name_hint = any(hint in lower for hint in name_hints)
    all_unique = len(values) == len(set(values)) and all(v.strip() for v in values)
    return has_name_hint and all_unique


def infer_schema(file_content: bytes, max_rows: int = 100) -> tuple[list[InferredColumn], int]:
    """
    Analyze a CSV file and return inferred column schemas.

    Returns (columns, total_row_count_in_sample).
    """
    text = file_content.decode("utf-8-sig")  # handle BOM
    reader = csv.DictReader(io.StringIO(text))
    fieldnames = reader.fieldnames or []

    # Collect samples per column
    samples: dict[str, list[str]] = {name: [] for name in fieldnames}
    row_count = 0
    for row in reader:
        if row_count >= max_rows:
            break
        for name in fieldnames:
            val = (row.get(name) or "").strip()
            if val:
                samples[name].append(val)
        row_count += 1

    columns: list[InferredColumn] = []
    for name in fieldnames:
        values = samples[name]
        columns.append(
            InferredColumn(
                original_name=name,
                inferred_type=_infer_type(values),
                suggested_display_name=_slugify(name),
                is_primary_key_candidate=_is_primary_key_candidate(name, values),
            )
        )

    return columns, row_count
