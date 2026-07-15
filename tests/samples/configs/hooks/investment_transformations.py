from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel, Field

from semantic_finance_etl.contracts.hook import TableHook
from semantic_finance_etl.domain.enums.hook_stage import HookStage
from semantic_finance_etl.domain.models.hook_payloads import BatchPayload, ExecutionContext
from semantic_finance_etl.domain.models.hook_results import (
    HookExecutionResult,
    HookMetrics,
    HookSchemaImpact,
)


class NormalizeInvestmentTransactionsParams(BaseModel):
    drop_zero_quantity: bool = Field(default=True)
    uppercase_symbol: bool = Field(default=True)
    trim_account_name: bool = Field(default=True)
    allowed_transaction_types: list[str] = Field(
        default_factory=lambda: ["BUY", "SELL", "DIVIDEND", "BONUS"]
    )


class NormalizeInvestmentTransactionsHook(
    TableHook[BatchPayload, BatchPayload, NormalizeInvestmentTransactionsParams]
):
    hook_name: ClassVar[str] = "normalize_investment_transactions"
    stage: ClassVar[HookStage] = HookStage.POST_APPEND
    params_model = NormalizeInvestmentTransactionsParams

    supported_table_names: ClassVar[set[str]] = {"investment_transactions"}

    required_columns: ClassVar[set[str]] = {
        "trade_date",
        "symbol",
        "transaction_type",
        "quantity",
        "amount",
        "account_name",
    }

    produced_columns: ClassVar[set[str]] = {
        "trade_date",
        "symbol",
        "transaction_type",
        "quantity",
        "amount",
        "account_name",
    }

    preserves_schema: ClassVar[bool] = True
    may_change_row_count: ClassVar[bool] = True

    def execute(
        self,
        context: ExecutionContext,
        payload: BatchPayload,
        params: NormalizeInvestmentTransactionsParams,
    ) -> HookExecutionResult[BatchPayload]:
        df = payload.frame

        # Placeholder implementation for now.
        # Later you can replace this block with real Polars logic such as:
        # - trimming account_name
        # - uppercasing symbol
        # - filtering zero quantities
        # - filtering transaction_type based on allowed_transaction_types

        updated_payload = payload.with_frame(df)

        return HookExecutionResult(
            payload=updated_payload,
            warnings=[],
            metrics=HookMetrics(
                rows_in=None,
                rows_out=None,
                timing_ms=None,
            ),
            schema_impact=HookSchemaImpact(
                schema_changed=False,
                columns_added=[],
                columns_removed=[],
                columns_renamed={},
            ),
            lineage_annotations={
                "hook_name": self.hook_name,
                "table_name": context.table_name or "",
                "source_id": context.source_id or "",
            },
        )


class AssignInvestmentIdsParams(BaseModel):
    id_prefix: str = Field(default="INV")


class AssignInvestmentIdsHook(
    TableHook[BatchPayload, BatchPayload, AssignInvestmentIdsParams]
):
    hook_name: ClassVar[str] = "assign_investment_ids"
    stage: ClassVar[HookStage] = HookStage.PRE_LOAD
    params_model = AssignInvestmentIdsParams

    supported_table_names: ClassVar[set[str]] = {"investment_transactions"}

    required_columns: ClassVar[set[str]] = {"trade_date", "symbol", "account_name"}
    produced_columns: ClassVar[set[str]] = {"canonical_id"}

    preserves_schema: ClassVar[bool] = False
    may_change_row_count: ClassVar[bool] = False

    def execute(
        self,
        context: ExecutionContext,
        payload: BatchPayload,
        params: AssignInvestmentIdsParams,
    ) -> HookExecutionResult[BatchPayload]:
        df = payload.frame

        # Placeholder implementation for now.
        # Later replace with real dataframe logic that adds canonical_id.

        updated_payload = payload.with_frame(df)

        return HookExecutionResult(
            payload=updated_payload,
            metrics=HookMetrics(
                rows_in=None,
                rows_out=None,
                timing_ms=None,
            ),
            schema_impact=HookSchemaImpact(
                schema_changed=True,
                columns_added=["canonical_id"],
                columns_removed=[],
                columns_renamed={},
            ),
            lineage_annotations={
                "hook_name": self.hook_name,
                "id_prefix": params.id_prefix,
            },
        )
