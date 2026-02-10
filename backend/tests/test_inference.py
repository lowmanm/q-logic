"""Tests for the schema inference engine."""

import pytest

from app.services.inference import infer_schema


def _make_csv(headers: list[str], rows: list[list[str]]) -> bytes:
    lines = [",".join(headers)]
    for row in rows:
        lines.append(",".join(row))
    return "\n".join(lines).encode("utf-8")


def test_infer_integer_column():
    csv = _make_csv(["id", "name"], [["1", "Alice"], ["2", "Bob"], ["3", "Charlie"]])
    columns, count = infer_schema(csv)
    assert count == 3
    assert columns[0].original_name == "id"
    assert columns[0].inferred_type == "INTEGER"
    assert columns[1].inferred_type == "STRING"


def test_infer_float_column():
    csv = _make_csv(["price"], [["9.99"], ["12.50"], ["3.14"]])
    columns, _ = infer_schema(csv)
    assert columns[0].inferred_type == "FLOAT"


def test_infer_boolean_column():
    csv = _make_csv(["active"], [["true"], ["false"], ["yes"], ["no"]])
    columns, _ = infer_schema(csv)
    assert columns[0].inferred_type == "BOOLEAN"


def test_infer_date_column():
    csv = _make_csv(
        ["created"],
        [["2024-01-15"], ["2024-02-20"], ["2024-03-10"]],
    )
    columns, _ = infer_schema(csv)
    assert columns[0].inferred_type == "DATE"


def test_primary_key_candidate():
    csv = _make_csv(
        ["account_id", "name"],
        [["A001", "Alice"], ["A002", "Bob"], ["A003", "Charlie"]],
    )
    columns, _ = infer_schema(csv)
    assert columns[0].is_primary_key_candidate is True
    assert columns[1].is_primary_key_candidate is False


def test_display_name_slugification():
    csv = _make_csv(["first_name", "lastName"], [["Alice", "Smith"]])
    columns, _ = infer_schema(csv)
    assert columns[0].suggested_display_name == "First Name"
    assert columns[1].suggested_display_name == "Last Name"


def test_empty_csv():
    csv = b"col_a,col_b\n"
    columns, count = infer_schema(csv)
    assert count == 0
    assert len(columns) == 2
    assert all(c.inferred_type == "STRING" for c in columns)


def test_respects_max_rows():
    rows = [[str(i), f"name_{i}"] for i in range(200)]
    csv = _make_csv(["id", "name"], rows)
    columns, count = infer_schema(csv, max_rows=50)
    assert count == 50
