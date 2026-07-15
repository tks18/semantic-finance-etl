from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

PayloadT = TypeVar("PayloadT")


class HookMetrics(BaseModel):
    rows_in: int | None = None
    rows_out: int | None = None
    timing_ms: float | None = None


class HookSchemaImpact(BaseModel):
    schema_changed: bool = False
    columns_added: list[str] = Field(default_factory=list)
    columns_removed: list[str] = Field(default_factory=list)
    columns_renamed: dict[str, str] = Field(default_factory=dict)


class HookExecutionResult(BaseModel, Generic[PayloadT]):
    payload: PayloadT
    warnings: list[str] = Field(default_factory=list)
    metrics: HookMetrics = Field(default_factory=HookMetrics)
    schema_impact: HookSchemaImpact = Field(default_factory=HookSchemaImpact)
    lineage_annotations: dict[str, str] = Field(default_factory=dict)
