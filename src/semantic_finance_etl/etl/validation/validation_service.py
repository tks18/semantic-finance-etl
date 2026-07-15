from __future__ import annotations

from typing import Any

from semantic_finance_etl.domain.models.hook_payloads import (
    BatchPayload,
    ValidatedBatchPayload,
)
from semantic_finance_etl.domain.models.runtime_table_definition import (
    RuntimeTableDefinition,
)


class ValidationService:
    def validate_batch(
        self,
        batch_payload: BatchPayload,
        runtime_table: RuntimeTableDefinition,
    ) -> ValidatedBatchPayload:
        frame = batch_payload.frame

        if frame is None:
            frame = []

        if not isinstance(frame, list):
            raise ValueError(
                "ValidationService currently expects batch frame to be list[dict[str, Any]]."
            )

        valid_rows: list[dict[str, Any]] = []
        invalid_rows: list[dict[str, Any]] = []
        validation_errors: list[dict[str, Any]] = []

        expected_columns = runtime_table.columns_by_name

        for row_index, row in enumerate(frame):
            if not isinstance(row, dict):
                invalid_rows.append({"__raw__": row})
                validation_errors.append(
                    {
                        "row_index": row_index,
                        "errors": ["Row is not a dict/object."],
                    }
                )
                continue

            row_errors: list[str] = []

            for column_name, column_def in expected_columns.items():
                value = row.get(column_name)

                if value is None:
                    if not column_def.nullable and column_def.default is None:
                        row_errors.append(
                            f"Column '{column_name}' is required but value is null/missing."
                        )
                    continue

                if not self._is_value_compatible(value, column_def.type_name):
                    row_errors.append(
                        f"Column '{column_name}' expected type '{column_def.type_name}' "
                        f"but got value '{value}' of type '{type(value).__name__}'."
                    )

            if row_errors:
                invalid_rows.append(row)
                validation_errors.append(
                    {
                        "row_index": row_index,
                        "errors": row_errors,
                    }
                )
            else:
                normalized_row = self._apply_defaults(row, runtime_table)
                valid_rows.append(normalized_row)

        return ValidatedBatchPayload(
            table_name=batch_payload.table_name,
            frame=valid_rows,
            validation_summary={
                "total_rows": len(frame),
                "valid_rows": len(valid_rows),
                "invalid_rows": len(invalid_rows),
                "errors": validation_errors,
            },
            target_schema={
                column.name: column.type_name for column in runtime_table.columns
            },
            valid_row_count=len(valid_rows),
            invalid_row_count=len(invalid_rows),
            lineage_refs=batch_payload.lineage_refs,
        )

    def _apply_defaults(
        self,
        row: dict[str, Any],
        runtime_table: RuntimeTableDefinition,
    ) -> dict[str, Any]:
        normalized = dict(row)

        for column in runtime_table.columns:
            if column.name not in normalized or normalized[column.name] is None:
                if column.default is not None:
                    normalized[column.name] = column.default

        return normalized

    def _is_value_compatible(self, value: Any, type_name: str) -> bool:
        normalized_type = type_name.strip().lower()

        if normalized_type in {"str", "string", "text"}:
            return isinstance(value, str)

        if normalized_type in {"int", "integer"}:
            return isinstance(value, int) and not isinstance(value, bool)

        if normalized_type in {"float", "double", "real"}:
            return isinstance(value, (int, float)) and not isinstance(value, bool)

        if normalized_type in {"bool", "boolean"}:
            return isinstance(value, bool)

        if normalized_type in {"decimal", "numeric", "number"}:
            return isinstance(value, (int, float)) and not isinstance(value, bool)

        if normalized_type in {"date", "datetime", "timestamp"}:
            return isinstance(value, str)

        if normalized_type in {"bytes", "blob"}:
            return isinstance(value, bytes)

        return True
