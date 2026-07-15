from __future__ import annotations

from typing import Any

from semantic_finance_etl.config.models.project_config import ProjectConfig
from semantic_finance_etl.domain.enums.hook_stage import HookStage
from semantic_finance_etl.domain.models.hook_payloads import ExecutionContext


class HookContextFactory:
    def create(
        self,
        *,
        project_config: ProjectConfig,
        run_id: str,
        stage: HookStage,
        table_name: str | None = None,
        source_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ExecutionContext:
        return ExecutionContext(
            run_id=run_id,
            project_id=project_config.project.project_id,
            table_name=table_name,
            source_id=source_id,
            stage=stage.value,
            metadata=metadata or {},
        )
