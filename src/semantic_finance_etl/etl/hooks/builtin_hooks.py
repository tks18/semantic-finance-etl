from __future__ import annotations

import hashlib
from typing import ClassVar

import polars as pl
from pydantic import BaseModel, Field

from semantic_finance_etl.contracts.hook import TableHook
from semantic_finance_etl.domain.enums.hook_stage import HookStage
from semantic_finance_etl.domain.models.hook_payloads import BatchPayload, ExecutionContext
from semantic_finance_etl.domain.models.hook_results import (
    HookExecutionResult,
    HookMetrics,
    HookSchemaImpact,
)


class ConcatKeyParams(BaseModel):
    source_columns: list[str]
    target_column: str
    separator: str = "_"


class ConcatKeyHook(TableHook[BatchPayload, BatchPayload, ConcatKeyParams]):
    """Concatenates multiple columns into a single string column (e.g. for composite keys)."""

    hook_name: ClassVar[str] = "builtin_concat_key"
    stage: ClassVar[HookStage] = HookStage.PRE_LOAD
    params_model = ConcatKeyParams

    def execute(
        self,
        context: ExecutionContext,
        payload: BatchPayload,
        params: ConcatKeyParams,
    ) -> HookExecutionResult[BatchPayload]:
        if payload.frame is None:
            return HookExecutionResult(
                payload=payload,
                metrics=HookMetrics(rows_in=0, rows_out=0),
                schema_impact=HookSchemaImpact(schema_changed=False),
            )

        expr = pl.concat_str([pl.col(c).fill_null("") for c in params.source_columns], separator=params.separator)
        df = payload.frame.with_columns(expr.alias(params.target_column))

        updated = payload.with_frame(df)

        return HookExecutionResult(
            payload=updated,
            metrics=HookMetrics(rows_in=None, rows_out=None),
            schema_impact=HookSchemaImpact(
                schema_changed=True,
                columns_added=[params.target_column],
                columns_removed=[],
                columns_renamed={},
            ),
        )


class HashRecordParams(BaseModel):
    target_column: str = "_record_hash"
    exclude_columns: list[str] = Field(
        default_factory=lambda: ["_file_hash", "_source_file", "_loaded_at", "_record_hash"]
    )


class HashRecordHook(TableHook[BatchPayload, BatchPayload, HashRecordParams]):
    """Creates a deterministic hash of the row (useful for idempotency without natural primary keys)."""

    hook_name: ClassVar[str] = "builtin_hash_record"
    stage: ClassVar[HookStage] = HookStage.PRE_LOAD
    params_model = HashRecordParams

    def execute(
        self,
        context: ExecutionContext,
        payload: BatchPayload,
        params: HashRecordParams,
    ) -> HookExecutionResult[BatchPayload]:
        if payload.frame is None:
            return HookExecutionResult(
                payload=payload,
                metrics=HookMetrics(rows_in=0, rows_out=0),
                schema_impact=HookSchemaImpact(schema_changed=False),
            )

        schema = payload.frame.collect_schema()
        cols_to_hash = [name for name in schema.names() if name not in (params.exclude_columns or [])]

        # Use version-independent SHA256 hashing
        expr = pl.concat_str([pl.col(c).cast(pl.Utf8).fill_null("") for c in cols_to_hash], separator="|").map_elements(
            lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest(), return_dtype=pl.Utf8
        )
        df = payload.frame.with_columns(expr.alias(params.target_column))

        updated = payload.with_frame(df)

        return HookExecutionResult(
            payload=updated,
            metrics=HookMetrics(rows_in=None, rows_out=None),
            schema_impact=HookSchemaImpact(
                schema_changed=True,
                columns_added=[params.target_column],
                columns_removed=[],
                columns_renamed={},
            ),
        )
