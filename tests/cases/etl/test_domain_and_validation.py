"""
pytest tests — ETL domain models (payloads + validation)
Tests the LazyFrame-native payload types and two-level ValidationService
using in-memory Polars frames (no file I/O needed).
"""
from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from semantic_finance_etl.domain.models.hook_payloads import (
    BatchPayload,
    DiscoveredAsset,
    DerivedBuildPayload,
    ReadPayload,
    ValidatedBatchPayload,
)
from semantic_finance_etl.domain.models.runtime_table_definition import (
    RuntimeColumnDefinition,
    RuntimeTableDefinition,
)
from semantic_finance_etl.etl.validation.validation_service import (
    ValidationService,
    SchemaValidationResult,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_asset(path: str = "/test/file.db") -> DiscoveredAsset:
    return DiscoveredAsset(path=path, source_id="test_src")


def _make_runtime_table(
    cols: list[tuple[str, str, bool]] | None = None,
    pk: list[str] | None = None,
) -> RuntimeTableDefinition:
    """cols = [(name, type, nullable)]"""
    if cols is None:
        cols = [("id", "int", False), ("name", "str", True), ("value", "float", True)]
    return RuntimeTableDefinition(
        table_name="test_table",
        table_kind="canonical",
        columns=[
            RuntimeColumnDefinition(name=c[0], type_name=c[1], nullable=c[2])
            for c in cols
        ],
        primary_key_fields=pk or [],
        load_mode="append",
    )


# ---------------------------------------------------------------------------
# ReadPayload
# ---------------------------------------------------------------------------

class TestReadPayload:
    def test_frame_is_lazy(self):
        lf = pl.DataFrame({"a": [1, 2, 3]}).lazy()
        payload = ReadPayload(asset=_make_asset(), frame=lf)
        assert isinstance(payload.frame, pl.LazyFrame)

    def test_collect_returns_dataframe(self):
        lf = pl.DataFrame({"a": [1, 2]}).lazy()
        payload = ReadPayload(asset=_make_asset(), frame=lf)
        df = payload.collect()
        assert isinstance(df, pl.DataFrame)
        assert len(df) == 2

    def test_with_frame_returns_new_payload(self):
        lf1 = pl.DataFrame({"a": [1]}).lazy()
        lf2 = pl.DataFrame({"b": [2]}).lazy()
        payload = ReadPayload(asset=_make_asset(), frame=lf1)
        updated = payload.with_frame(lf2)
        assert updated is not payload
        assert list(updated.frame.collect_schema().names()) == ["b"]


# ---------------------------------------------------------------------------
# BatchPayload
# ---------------------------------------------------------------------------

class TestBatchPayload:
    def test_frame_is_lazy(self):
        lf = pl.DataFrame({"x": [10, 20]}).lazy()
        batch = BatchPayload(table_name="t", frame=lf)
        assert isinstance(batch.frame, pl.LazyFrame)

    def test_collect_returns_empty_when_frame_is_none(self):
        batch = BatchPayload(table_name="t", frame=None)
        df = batch.collect()
        assert isinstance(df, pl.DataFrame)
        assert len(df) == 0

    def test_lineage_refs_preserved(self):
        lf = pl.DataFrame({"a": [1]}).lazy()
        batch = BatchPayload(table_name="t", frame=lf, lineage_refs=["src1", "src2"])
        assert batch.lineage_refs == ["src1", "src2"]


# ---------------------------------------------------------------------------
# ValidationService — Level 1: schema validation (lazy)
# ---------------------------------------------------------------------------

class TestSchemaValidation:
    def test_valid_schema_passes(self):
        lf = pl.DataFrame({"id": [1, 2], "name": ["a", "b"], "value": [1.0, 2.0]}).lazy()
        batch = BatchPayload(table_name="test_table", frame=lf)
        rt = _make_runtime_table()
        result = ValidationService().validate_schema(batch, rt)
        assert result.is_valid

    def test_missing_required_column_raises_error(self):
        # 'id' is non-nullable — missing from frame
        lf = pl.DataFrame({"name": ["a", "b"], "value": [1.0, 2.0]}).lazy()
        batch = BatchPayload(table_name="test_table", frame=lf)
        rt = _make_runtime_table()
        result = ValidationService().validate_schema(batch, rt)
        assert not result.is_valid
        error_cols = [i.column for i in result.error_issues]
        assert "id" in error_cols

    def test_missing_nullable_column_is_warning_not_error(self):
        # 'name' is nullable — should produce a warning, not an error
        lf = pl.DataFrame({"id": [1], "value": [1.0]}).lazy()
        batch = BatchPayload(table_name="test_table", frame=lf)
        rt = _make_runtime_table()
        result = ValidationService().validate_schema(batch, rt)
        assert result.is_valid  # only warnings, no errors
        assert any(i.severity == "warning" for i in result.issues)

    def test_missing_pk_column_is_error(self):
        lf = pl.DataFrame({"name": ["a"]}).lazy()
        batch = BatchPayload(table_name="test_table", frame=lf)
        rt = _make_runtime_table(pk=["id"])
        result = ValidationService().validate_schema(batch, rt)
        assert not result.is_valid

    def test_none_frame_returns_error(self):
        batch = BatchPayload(table_name="test_table", frame=None)
        rt = _make_runtime_table()
        result = ValidationService().validate_schema(batch, rt)
        assert not result.is_valid


# ---------------------------------------------------------------------------
# ValidationService — Level 2: data validation (collects)
# ---------------------------------------------------------------------------

class TestDataValidation:
    def test_all_valid_rows_pass(self):
        lf = pl.DataFrame({"id": [1, 2], "name": ["a", "b"], "value": [1.0, 2.0]}).lazy()
        batch = BatchPayload(table_name="test_table", frame=lf)
        rt = _make_runtime_table()
        validated = ValidationService().validate_batch(batch, rt)
        assert validated.valid_row_count == 2
        assert validated.invalid_row_count == 0
        assert validated.invalid_frame is None

    def test_null_in_required_column_goes_to_invalid(self):
        lf = pl.DataFrame({"id": [1, None], "name": ["a", "b"], "value": [1.0, 2.0]}).lazy()
        batch = BatchPayload(table_name="test_table", frame=lf)
        rt = _make_runtime_table()
        validated = ValidationService().validate_batch(batch, rt)
        assert validated.valid_row_count == 1
        assert validated.invalid_row_count == 1

    def test_valid_frame_stays_lazy(self):
        lf = pl.DataFrame({"id": [1], "name": ["a"], "value": [1.0]}).lazy()
        batch = BatchPayload(table_name="test_table", frame=lf)
        rt = _make_runtime_table()
        validated = ValidationService().validate_batch(batch, rt)
        assert isinstance(validated.valid_frame, pl.LazyFrame)

    def test_invalid_frame_stays_lazy_when_present(self):
        lf = pl.DataFrame({"id": [None], "name": ["a"], "value": [1.0]}).lazy()
        batch = BatchPayload(table_name="test_table", frame=lf)
        rt = _make_runtime_table()
        validated = ValidationService().validate_batch(batch, rt)
        assert isinstance(validated.invalid_frame, pl.LazyFrame)

    def test_pk_duplicate_goes_to_invalid(self):
        lf = pl.DataFrame({
            "id": [1, 1],  # duplicate PK
            "name": ["a", "b"],
            "value": [1.0, 2.0],
        }).lazy()
        batch = BatchPayload(table_name="test_table", frame=lf)
        rt = _make_runtime_table(pk=["id"])
        validated = ValidationService().validate_batch(batch, rt)
        assert validated.invalid_row_count >= 1

    def test_none_frame_returns_empty_valid(self):
        batch = BatchPayload(table_name="test_table", frame=None)
        rt = _make_runtime_table()
        validated = ValidationService().validate_batch(batch, rt)
        assert validated.valid_row_count == 0
        df = validated.valid_frame.collect()
        assert len(df) == 0
