from __future__ import annotations

from typing import ClassVar

import polars as pl
from pydantic import BaseModel, Field

from semantic_finance_etl.contracts.hook import TableHook, DerivedTableHook
from semantic_finance_etl.domain.enums.hook_stage import HookStage
from semantic_finance_etl.domain.models.hook_payloads import BatchPayload, DerivedBuildPayload, ExecutionContext
from semantic_finance_etl.domain.models.hook_results import (
    HookExecutionResult,
    HookMetrics,
    HookSchemaImpact,
)

class CleanCompaniesDataParams(BaseModel):
    fill_year: int = Field(default=1900)
    fill_industry: str = Field(default="Unknown")
    fill_employees: int = Field(default=0)


class CleanCompaniesDataHook(
    TableHook[BatchPayload, BatchPayload, CleanCompaniesDataParams]
):
    hook_name: ClassVar[str] = "clean_companies_data"
    stage: ClassVar[HookStage] = HookStage.POST_APPEND
    params_model = CleanCompaniesDataParams

    supported_table_names: ClassVar[set[str]] = {"companies"}

    required_columns: ClassVar[set[str]] = {
        "id", "year_founded", "industry", "current_employees", "total_employees"
    }

    produced_columns: ClassVar[set[str]] = set()

    def execute(
        self,
        context: ExecutionContext,
        payload: BatchPayload,
        params: CleanCompaniesDataParams,
    ) -> HookExecutionResult[BatchPayload]:
        df = payload.frame

        if df is not None:
            df = df.with_columns([
                pl.col("year_founded").cast(pl.Int32, strict=False).fill_null(params.fill_year),
                pl.col("industry").fill_null(params.fill_industry).str.to_uppercase(),
                pl.col("current_employees").cast(pl.Int32, strict=False).fill_null(params.fill_employees),
                pl.col("total_employees").cast(pl.Int32, strict=False).fill_null(params.fill_employees),
            ])

        updated_payload = payload.with_frame(df)

        return HookExecutionResult(
            payload=updated_payload,
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
            },
        )


class BuildIndustryStatsParams(BaseModel):
    pass


class BuildIndustryStatsHook(
    DerivedTableHook[DerivedBuildPayload, DerivedBuildPayload, BuildIndustryStatsParams]
):
    hook_name: ClassVar[str] = "build_industry_stats"
    stage: ClassVar[HookStage] = HookStage.POST_DERIVE
    params_model = BuildIndustryStatsParams

    supported_table_names: ClassVar[set[str]] = {"industry_stats"}

    required_columns: ClassVar[set[str]] = set()
    produced_columns: ClassVar[set[str]] = {
        "industry", "company_count", "total_employees", "avg_year_founded"
    }

    def execute(
        self,
        context: ExecutionContext,
        payload: DerivedBuildPayload,
        params: BuildIndustryStatsParams,
    ) -> HookExecutionResult[DerivedBuildPayload]:
        # 'companies' is our dependency
        companies_df = payload.dependency_frames.get("companies")
        if companies_df is None:
            raise ValueError("Missing 'companies' dependency for industry_stats build.")

        # Aggregate stats
        agg_df = companies_df.group_by("industry").agg([
            pl.len().alias("company_count"),
            pl.col("current_employees").sum().alias("total_employees"),
            pl.col("year_founded").mean().cast(pl.Int32).alias("avg_year_founded"),
        ])

        updated_payload = payload.with_output_frame(agg_df)

        return HookExecutionResult(
            payload=updated_payload,
            metrics=HookMetrics(
                rows_in=None,
                rows_out=None,
                timing_ms=None,
            ),
            schema_impact=HookSchemaImpact(
                schema_changed=True,
                columns_added=["industry", "company_count", "total_employees", "avg_year_founded"],
                columns_removed=[],
                columns_renamed={},
            ),
            lineage_annotations={
                "hook_name": self.hook_name,
            },
        )
