from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

from semantic_finance_etl.config.services.project_config_service import (
    ProjectConfigService,
)
from semantic_finance_etl.infrastructure.plugins.local_plugin_registry import (
    LocalPluginRegistry,
)
from semantic_finance_etl.tables.configured_table_pipeline import (
    ConfiguredTablePipeline,
    TablePipelineExecutionResult,
)


@dataclass(slots=True)
class PipelineExecutionSummary:
    run_id: str
    pipeline_results: list[TablePipelineExecutionResult] = field(default_factory=list)


class PipelineExecutor:
    def __init__(
        self,
        *,
        config_service: ProjectConfigService | None = None,
        hook_registry: LocalPluginRegistry | None = None,
        configured_table_pipeline: ConfiguredTablePipeline | None = None,
    ) -> None:
        self._config_service = config_service or ProjectConfigService()
        self._hook_registry = hook_registry or LocalPluginRegistry()
        self._configured_table_pipeline = configured_table_pipeline

    def run(
        self,
        config_root: str | Path,
    ) -> PipelineExecutionSummary:
        project_config = self._config_service.load(config_root)
        run_id = str(uuid4())

        self._hook_registry.register_from_search_paths(
            project_config.runtime.hook_search_paths
        )

        pipeline = self._configured_table_pipeline or ConfiguredTablePipeline(
            hook_registry=self._hook_registry
        )

        tables_by_name = {
            table.table_name: table
            for table in project_config.tables
        }

        results: list[TablePipelineExecutionResult] = []

        for source in project_config.sources:
            for target_table_name in source.target_tables:
                table = tables_by_name[target_table_name]

                result = pipeline.run(
                    project_config=project_config,
                    source_config=source,
                    table_config=table,
                    run_id=run_id,
                )
                results.append(result)

        return PipelineExecutionSummary(
            run_id=run_id,
            pipeline_results=results,
        )
