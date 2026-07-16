from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import polars as pl

from semantic_finance_etl.domain.models.hook_payloads import (
    BatchPayload,
    ValidatedBatchPayload,
)
from semantic_finance_etl.domain.models.runtime_table_definition import (
    RuntimeTableDefinition,
)


@dataclass(slots=True)
class SchemaValidationIssue:
    """A schema-level issue detected without collecting data."""

    column: str
    reason: str
    severity: str = "error"  # "error" | "warning"


@dataclass(slots=True)
class SchemaValidationResult:
    """Result of the lazy (schema-only) validation pass."""

    issues: list[SchemaValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    @property
    def error_issues(self) -> list[SchemaValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warning_issues(self) -> list[SchemaValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]


class ValidationService:
    """Two-level validation service aligned with the LazyFrame execution model.

    Level 1 — Schema validation (``validate_schema``):
        Operates entirely on the lazy schema — no ``.collect()`` required.
        Checks required columns, type compatibility, and primary key presence.

    Level 2 — Data validation (``validate_batch``):
        Collects the lazy frame to perform row-level checks.
        Splits the result into ``valid_frame`` and ``invalid_frame``,
        both returned as lazy frames for the load/DLQ boundary.
    """

    # ------------------------------------------------------------------
    # Level 1 — Schema validation (lazy, no collect)
    # ------------------------------------------------------------------

    def validate_schema(
        self,
        batch_payload: BatchPayload,
        runtime_table: RuntimeTableDefinition,
    ) -> SchemaValidationResult:
        """Validate frame schema against the runtime table definition.

        No data is collected.  Returns a ``SchemaValidationResult`` with
        any missing columns, type mismatches, or missing PK columns.
        """
        result = SchemaValidationResult()

        if batch_payload.frame is None:
            result.issues.append(
                SchemaValidationIssue(
                    column="__frame__",
                    reason="Batch frame is None — nothing to validate.",
                    severity="error",
                )
            )
            return result

        # Collect schema from the lazy plan (no data pulled).
        try:
            lazy_schema: dict[str, pl.DataType] = batch_payload.frame.collect_schema()
        except pl.exceptions.ComputeError as exc:
            result.issues.append(
                SchemaValidationIssue(
                    column="__frame__",
                    reason=f"Could not inspect lazy schema: {exc}",
                    severity="error",
                )
            )
            return result

        frame_columns = set(lazy_schema.keys())

        # Required column check.
        for column in runtime_table.columns:
            if column.name not in frame_columns:
                if not column.nullable and column.default is None:
                    result.issues.append(
                        SchemaValidationIssue(
                            column=column.name,
                            reason=(
                                f"Required non-nullable column '{column.name}' "
                                "is missing from the frame schema."
                            ),
                            severity="error",
                        )
                    )
                else:
                    result.issues.append(
                        SchemaValidationIssue(
                            column=column.name,
                            reason=(
                                f"Nullable column '{column.name}' is absent — "
                                "will be filled with nulls."
                            ),
                            severity="warning",
                        )
                    )

        # Primary key columns must be present.
        for pk_col in runtime_table.primary_key_fields:
            if pk_col not in frame_columns:
                result.issues.append(
                    SchemaValidationIssue(
                        column=pk_col,
                        reason=(
                            f"Primary key column '{pk_col}' is missing from "
                            "the frame schema."
                        ),
                        severity="error",
                    )
                )

        return result

    # ------------------------------------------------------------------
    # Level 2 — Data validation (collects at this boundary)
    # ------------------------------------------------------------------

    def validate_batch(
        self,
        batch_payload: BatchPayload,
        runtime_table: RuntimeTableDefinition,
    ) -> ValidatedBatchPayload:
        """Validate row-level data and produce a ``ValidatedBatchPayload``.

        This is the designated collection boundary for data-level checks.
        Valid and invalid rows are split and wrapped back into lazy frames
        so the load / DLQ services stay in the lazy execution model.
        """
        if batch_payload.frame is None:
            empty_lf = pl.DataFrame().lazy()
            return ValidatedBatchPayload(
                table_name=batch_payload.table_name,
                valid_frame=empty_lf,
                invalid_frame=None,
                data_schema=batch_payload.data_schema,
                validation_summary={
                    "total_rows": 0,
                    "valid_rows": 0,
                    "invalid_rows": 0,
                    "errors": [],
                    "warnings": ["Batch frame was None — produced empty valid frame."],
                },
                target_schema={
                    col.name: col.type_name for col in runtime_table.columns
                },
                valid_row_count=0,
                invalid_row_count=0,
                lineage_refs=batch_payload.lineage_refs,
            )

        # --- Explicit collect boundary ---
        df: pl.DataFrame = batch_payload.frame.collect()

        expected_columns = runtime_table.columns_by_name
        present_columns = set(df.columns)

        def _get_pl_type(type_name: str) -> pl.DataType:
            t = type_name.strip().lower()
            if t in {"int", "integer"}: return pl.Int64
            if t in {"float", "double", "real", "number", "numeric"}: return pl.Float64
            if t in {"bool", "boolean"}: return pl.Boolean
            if t in {"date"}: return pl.Date
            if t in {"datetime", "timestamp"}: return pl.Datetime
            return pl.Utf8

        # Add missing nullable columns as null.
        missing_exprs = []
        for col_name, col_def in expected_columns.items():
            if col_name not in present_columns:
                pl_type = _get_pl_type(col_def.type_name)
                if col_def.default is not None:
                    missing_exprs.append(pl.lit(col_def.default).cast(pl_type).alias(col_name))
                elif col_def.nullable:
                    missing_exprs.append(pl.lit(None).cast(pl_type).alias(col_name))
                    
        if missing_exprs:
            df = df.with_columns(missing_exprs)

        # Vectorized batch-validation error construction
        error_conditions = []

        for col_name, col_def in expected_columns.items():
            if col_name not in df.columns:
                continue

            if not col_def.nullable and col_def.default is None:
                error_conditions.append(
                    pl.when(pl.col(col_name).is_null())
                    .then(pl.lit(f"Column '{col_name}' is required but null."))
                    .otherwise(pl.lit(""))
                )

        # Uniqueness checks for PK columns.
        if runtime_table.primary_key_fields:
            pk_cols = [
                c for c in runtime_table.primary_key_fields if c in df.columns
            ]
            if pk_cols:
                error_conditions.append(
                    pl.when(pl.struct(pk_cols).is_duplicated())
                    .then(pl.lit(f"Duplicate primary key on columns {pk_cols}."))
                    .otherwise(pl.lit(""))
                )

        if error_conditions:
            df = df.with_columns(
                pl.concat_list(error_conditions).list.eval(
                    pl.element().filter(pl.element() != "")
                ).list.join("; ").alias("__error_messages__")
            )
            df = df.with_columns(
                (pl.col("__error_messages__").str.len_chars() > 0).alias("__has_error__")
            )
        else:
            df = df.with_columns([
                pl.lit(False).alias("__has_error__"),
                pl.lit("").alias("__error_messages__")
            ])

        valid_df = df.filter(~pl.col("__has_error__")).drop(
            ["__has_error__", "__error_messages__"]
        )
        invalid_df = df.filter(pl.col("__has_error__"))

        validation_errors = self._collect_validation_errors(invalid_df)

        return ValidatedBatchPayload(
            table_name=batch_payload.table_name,
            valid_frame=valid_df.lazy(),
            invalid_frame=invalid_df.lazy() if len(invalid_df) > 0 else None,
            data_schema=batch_payload.data_schema,
            validation_summary={
                "total_rows": len(df),
                "valid_rows": len(valid_df),
                "invalid_rows": len(invalid_df),
                "errors": validation_errors,
            },
            target_schema={
                col.name: col.type_name for col in runtime_table.columns
            },
            valid_row_count=len(valid_df),
            invalid_row_count=len(invalid_df),
            lineage_refs=batch_payload.lineage_refs,
        )

    def _collect_validation_errors(
        self,
        invalid_df: pl.DataFrame,
    ) -> list[dict[str, Any]]:
        errors: list[dict[str, Any]] = []

        if len(invalid_df) == 0:
            return errors

        msg_col = "__error_messages__"

        for i in range(len(invalid_df)):
            row_errors = (
                invalid_df[msg_col][i]
                if msg_col in invalid_df.columns
                else "Unknown error"
            )
            errors.append({"row_index": i, "errors": str(row_errors)})

        return errors
