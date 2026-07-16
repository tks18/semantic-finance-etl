from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from semantic_finance_etl.domain.models.data_schema import DataSchema


class FrameEngine(StrEnum):
    POLARS_LAZY = "polars_lazy"


class SchemaMutationBehavior(StrEnum):
    PRESERVES_SCHEMA = "preserves_schema"
    ADDS_COLUMNS = "adds_columns"
    DROPS_COLUMNS = "drops_columns"
    REPLACES_SCHEMA = "replaces_schema"
    UNKNOWN = "unknown"


class CardinalityBehavior(StrEnum):
    PRESERVES_ROWS = "preserves_rows"
    FILTERS_ROWS = "filters_rows"
    MAY_EXPAND_ROWS = "may_expand_rows"
    AGGREGATES_ROWS = "aggregates_rows"
    UNKNOWN = "unknown"


class MaterializationPolicy(StrEnum):
    LAZY_PREFERRED = "lazy_preferred"
    MATERIALIZATION_ALLOWED = "materialization_allowed"
    MATERIALIZATION_REQUIRED = "materialization_required"


class FrameContract(BaseModel):
    engine: FrameEngine = FrameEngine.POLARS_LAZY
    input_schema: DataSchema | None = None
    output_schema: DataSchema | None = None

    requires_columns: list[str] = Field(default_factory=list)
    provides_columns: list[str] = Field(default_factory=list)

    schema_mutation: SchemaMutationBehavior = SchemaMutationBehavior.UNKNOWN
    cardinality: CardinalityBehavior = CardinalityBehavior.UNKNOWN
    materialization_policy: MaterializationPolicy = (
        MaterializationPolicy.LAZY_PREFERRED
    )

    def validate_input_schema(self, schema: DataSchema | None) -> None:
        if schema is None:
            if self.requires_columns:
                raise ValueError(
                    "Input schema is missing but required columns were declared."
                )
            return

        missing = [
            column_name
            for column_name in self.requires_columns
            if not schema.has_column(column_name)
        ]
        if missing:
            raise ValueError(
                f"Input schema is missing required columns: {missing}"
            )

        if self.input_schema is not None:
            diff = self.input_schema.compare_to(schema, strict_nullability=False)
            if diff.missing_in_right or diff.type_mismatches:
                raise ValueError(
                    "Input schema is incompatible with contract. "
                    f"Missing columns: {diff.missing_in_right}; "
                    f"type mismatches: {diff.type_mismatches}"
                )

    def validate_output_schema(self, schema: DataSchema | None) -> None:
        if self.output_schema is None or schema is None:
            return

        diff = self.output_schema.compare_to(schema, strict_nullability=False)
        if diff.missing_in_right or diff.type_mismatches:
            raise ValueError(
                "Output schema is incompatible with contract. "
                f"Missing columns: {diff.missing_in_right}; "
                f"type mismatches: {diff.type_mismatches}"
            )

    def describe(self) -> dict[str, object]:
        return {
            "engine": self.engine.value,
            "requires_columns": list(self.requires_columns),
            "provides_columns": list(self.provides_columns),
            "schema_mutation": self.schema_mutation.value,
            "cardinality": self.cardinality.value,
            "materialization_policy": self.materialization_policy.value,
            "has_input_schema": self.input_schema is not None,
            "has_output_schema": self.output_schema is not None,
        }
