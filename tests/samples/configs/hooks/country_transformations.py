from __future__ import annotations

from typing import ClassVar

import polars as pl
from pydantic import BaseModel

from semantic_finance_etl.contracts.hook import DerivedTableHook
from semantic_finance_etl.domain.enums.hook_stage import HookStage
from semantic_finance_etl.domain.models.hook_payloads import DerivedBuildPayload, ExecutionContext
from semantic_finance_etl.domain.models.hook_results import (
    HookExecutionResult,
    HookMetrics,
    HookSchemaImpact,
)

class BuildCountryIndustrySummaryParams(BaseModel):
    pass


class BuildCountryIndustrySummaryHook(
    DerivedTableHook[DerivedBuildPayload, DerivedBuildPayload, BuildCountryIndustrySummaryParams]
):
    hook_name: ClassVar[str] = "build_country_industry_summary"
    stage: ClassVar[HookStage] = HookStage.POST_DERIVE
    params_model = BuildCountryIndustrySummaryParams

    supported_table_names: ClassVar[set[str]] = {"country_industry_summary"}

    required_columns: ClassVar[set[str]] = set()
    produced_columns: ClassVar[set[str]] = {
        "country", "industry", "country_employees", "global_industry_employees", "percent_of_global"
    }

    def execute(
        self,
        context: ExecutionContext,
        payload: DerivedBuildPayload,
        params: BuildCountryIndustrySummaryParams,
    ) -> HookExecutionResult[DerivedBuildPayload]:
        companies_df = payload.dependency_frames.get("companies")
        industry_stats_df = payload.dependency_frames.get("industry_stats")

        if companies_df is None or industry_stats_df is None:
            raise ValueError("Missing dependencies for country_industry_summary build.")

        # Aggregate country employees by industry
        country_agg = companies_df.group_by(["country", "industry"]).agg([
            pl.col("current_employees").sum().alias("country_employees")
        ])

        # Join with industry stats
        joined = country_agg.join(
            industry_stats_df.select(["industry", "total_employees"]),
            on="industry",
            how="left"
        ).rename({"total_employees": "global_industry_employees"})

        # Calculate percentage
        final_df = joined.with_columns(
            pl.when(pl.col("global_industry_employees").fill_null(0) > 0)
            .then(pl.col("country_employees") / pl.col("global_industry_employees"))
            .otherwise(pl.lit(0.0))
            .alias("percent_of_global")
        )

        updated_payload = payload.with_output_frame(final_df)

        return HookExecutionResult(
            payload=updated_payload,
            metrics=HookMetrics(rows_in=None, rows_out=None, timing_ms=None),
            schema_impact=HookSchemaImpact(
                schema_changed=True,
                columns_added=["country", "industry", "country_employees", "global_industry_employees", "percent_of_global"],
                columns_removed=[],
                columns_renamed={},
            ),
            lineage_annotations={"hook_name": self.hook_name},
        )
