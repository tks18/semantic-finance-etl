from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from semantic_finance_etl.config.models.project_config import ProjectConfig
from semantic_finance_etl.domain.enums.hook_stage import HookStage
from semantic_finance_etl.domain.models.hook_payloads import ExecutionContext
from semantic_finance_etl.domain.models.hook_results import HookExecutionResult
from semantic_finance_etl.etl.hooks.hook_binding_resolver import ResolvedHookBinding
from semantic_finance_etl.etl.hooks.hook_context_factory import HookContextFactory

PayloadT = TypeVar("PayloadT")


@dataclass(slots=True)
class HookRunRecord(Generic[PayloadT]):
    hook_name: str
    stage: HookStage
    result: HookExecutionResult[PayloadT]


@dataclass(slots=True)
class HookRunSummary(Generic[PayloadT]):
    final_payload: PayloadT
    records: list[HookRunRecord[PayloadT]]


class HookRunner:
    def __init__(self, context_factory: HookContextFactory | None = None) -> None:
        self._context_factory = context_factory or HookContextFactory()

    def run_stage(
        self,
        *,
        project_config: ProjectConfig,
        run_id: str,
        stage: HookStage,
        payload: PayloadT,
        bindings: list[ResolvedHookBinding],
        table_name: str | None = None,
        source_id: str | None = None,
        metadata: dict | None = None,
    ) -> HookRunSummary[PayloadT]:
        current_payload = payload
        records: list[HookRunRecord[PayloadT]] = []

        for binding in bindings:
            context = self._context_factory.create(
                project_config=project_config,
                run_id=run_id,
                stage=stage,
                table_name=table_name,
                source_id=source_id,
                metadata=metadata or {},
            )

            hook_instance = binding.create_instance()
            result = hook_instance.execute(
                context=context,
                payload=current_payload,
                params=binding.params,
            )

            current_payload = result.payload
            records.append(
                HookRunRecord(
                    hook_name=binding.hook_name,
                    stage=stage,
                    result=result,
                )
            )

        return HookRunSummary(
            final_payload=current_payload,
            records=records,
        )
