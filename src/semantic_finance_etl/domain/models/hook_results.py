from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from semantic_finance_etl.domain.models.data_schema import DataSchema

PayloadT = TypeVar("PayloadT")


class HookMetrics(BaseModel):
    rows_in: int | None = None
    rows_out: int | None = None
    timing_ms: float | None = None


class HookSchemaImpact(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    schema_changed: bool = False
    columns_added: list[str] = Field(default_factory=list)
    columns_removed: list[str] = Field(default_factory=list)
    columns_renamed: dict[str, str] = Field(default_factory=dict)

    # Typed schema snapshots so downstream services can diff them precisely.
    before_schema: DataSchema | None = None
    after_schema: DataSchema | None = None


class HookExecutionResult(BaseModel, Generic[PayloadT]):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    payload: PayloadT
    warnings: list[str] = Field(default_factory=list)
    metrics: HookMetrics = Field(default_factory=HookMetrics)
    schema_impact: HookSchemaImpact = Field(default_factory=HookSchemaImpact)
    lineage_annotations: dict[str, str] = Field(default_factory=dict)
