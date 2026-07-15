from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from semantic_finance_etl.config.models.project_config import ProjectConfig
from semantic_finance_etl.config.models.source_config import SourceConfig
from semantic_finance_etl.config.models.table_config import TableConfig
from semantic_finance_etl.domain.enums.hook_stage import HookStage
from semantic_finance_etl.domain.models.hook_payloads import BatchPayload, ReadPayload
from semantic_finance_etl.etl.hooks.hook_binding_resolver import HookBindingResolver
from semantic_finance_etl.etl.hooks.hook_runner import HookRunSummary, HookRunner
from semantic_finance_etl.infrastructure.factories.source_component_factory import (
    SourceComponentFactory,
)
from semantic_finance_etl.infrastructure.plugins.local_plugin_registry import (
    LocalPluginRegistry,
)


@dataclass(slots=True)
class TablePipelineExecutionResult:
    run_id: str
    source_id: str
    table_name: str

    discovered_count: int = 0
    selected_count: int = 0
    group_count: int = 0
    read_payload_count: int = 0

    final_batch_payload: BatchPayload | None = None

    post_read_records: list[Any] = field(default_factory=list)
    post_append_records: list[Any] = field(default_factory=list)
    pre_load_records: list[Any] = field(default_factory=list)


class ConfiguredTablePipeline:
    def __init__(
        self,
        *,
        component_factory: SourceComponentFactory | None = None,
        hook_runner: HookRunner | None = None,
        hook_registry: LocalPluginRegistry | None = None,
    ) -> None:
        self._component_factory = component_factory or SourceComponentFactory()
        self._hook_runner = hook_runner or HookRunner()
        self._hook_registry = hook_registry or LocalPluginRegistry()

    def run(
        self,
        *,
        project_config: ProjectConfig,
        source_config: SourceConfig,
        table_config: TableConfig,
        run_id: str | None = None,
    ) -> TablePipelineExecutionResult:
        effective_run_id = run_id or str(uuid4())

        discoverer = self._component_factory.create_discoverer(source_config)
        selector = self._component_factory.create_selector(source_config)
        grouper = self._component_factory.create_grouper(source_config)
        reader = self._component_factory.create_reader(source_config)
        resolver = HookBindingResolver(self._hook_registry)

        discovered_assets = discoverer.discover(source_config)
        selected_assets = selector.select(source_config, discovered_assets)
        groups = grouper.group(source_config, selected_assets)

        result = TablePipelineExecutionResult(
            run_id=effective_run_id,
            source_id=source_config.source_id,
            table_name=table_config.table_name,
            discovered_count=len(discovered_assets),
            selected_count=len(selected_assets),
            group_count=len(groups),
        )

        read_payloads: list[ReadPayload] = []

        for group in groups:
            group_read_payloads = reader.read_group(
                source_config=source_config,
                reader_config=source_config.reader,
                group=group,
            )

            for read_payload in group_read_payloads:
                resolved_post_read = resolver.resolve_bindings_for_stage(
                    stage=HookStage.POST_READ,
                    bindings=source_config.hooks.post_read,
                )

                if resolved_post_read:
                    post_read_summary = self._hook_runner.run_stage(
                        project_config=project_config,
                        run_id=effective_run_id,
                        stage=HookStage.POST_READ,
                        payload=read_payload,
                        bindings=resolved_post_read,
                        table_name=table_config.table_name,
                        source_id=source_config.source_id,
                        metadata={"group_id": group.group_id},
                    )
                    read_payload = post_read_summary.final_payload
                    result.post_read_records.extend(post_read_summary.records)

                read_payloads.append(read_payload)

        result.read_payload_count = len(read_payloads)

        combined_rows = self._append_read_payload_frames(read_payloads)

        batch_payload = BatchPayload(
            table_name=table_config.table_name,
            source_id=source_config.source_id,
            frame=combined_rows,
            assets=[payload.asset for payload in read_payloads],
            combine_strategy="append_rows",
            inferred_schema=self._merge_inferred_schemas(read_payloads),
            lineage_refs=self._collect_lineage_refs(read_payloads),
            batch_metadata={
                "read_payload_count": len(read_payloads),
                "source_id": source_config.source_id,
                "table_name": table_config.table_name,
            },
        )

        resolved_post_append = resolver.resolve_bindings_for_stage(
            stage=HookStage.POST_APPEND,
            bindings=[
                *source_config.hooks.post_append,
                *table_config.hooks.post_append,
            ],
        )

        if resolved_post_append:
            post_append_summary = self._hook_runner.run_stage(
                project_config=project_config,
                run_id=effective_run_id,
                stage=HookStage.POST_APPEND,
                payload=batch_payload,
                bindings=resolved_post_append,
                table_name=table_config.table_name,
                source_id=source_config.source_id,
            )
            batch_payload = post_append_summary.final_payload
            result.post_append_records.extend(post_append_summary.records)

        resolved_pre_load = resolver.resolve_bindings_for_stage(
            stage=HookStage.PRE_LOAD,
            bindings=[
                *source_config.hooks.pre_load,
                *table_config.hooks.pre_load,
            ],
        )

        if resolved_pre_load:
            pre_load_summary = self._hook_runner.run_stage(
                project_config=project_config,
                run_id=effective_run_id,
                stage=HookStage.PRE_LOAD,
                payload=batch_payload,
                bindings=resolved_pre_load,
                table_name=table_config.table_name,
                source_id=source_config.source_id,
            )
            batch_payload = pre_load_summary.final_payload
            result.pre_load_records.extend(pre_load_summary.records)

        result.final_batch_payload = batch_payload
        return result

    def _append_read_payload_frames(
        self,
        read_payloads: list[ReadPayload],
    ) -> list[dict[str, Any]]:
        combined: list[dict[str, Any]] = []

        for payload in read_payloads:
            frame = payload.frame

            if frame is None:
                continue

            if not isinstance(frame, list):
                raise ValueError(
                    "Current ConfiguredTablePipeline expects read payload frame to be "
                    "a list[dict[str, Any]]."
                )

            for row in frame:
                if not isinstance(row, dict):
                    raise ValueError(
                        "Current ConfiguredTablePipeline expects each frame row to be a dict."
                    )
                combined.append(row)

        return combined

    def _merge_inferred_schemas(
        self,
        read_payloads: list[ReadPayload],
    ) -> dict[str, str]:
        merged: dict[str, str] = {}

        for payload in read_payloads:
            for column_name, type_name in payload.inferred_schema.items():
                merged.setdefault(column_name, type_name)

        return merged

    def _collect_lineage_refs(
        self,
        read_payloads: list[ReadPayload],
    ) -> list[str]:
        lineage_refs: list[str] = []

        for payload in read_payloads:
            lineage_refs.extend(payload.lineage_refs)

        # preserve order while removing duplicates
        seen: set[str] = set()
        unique_refs: list[str] = []

        for ref in lineage_refs:
            if ref not in seen:
                seen.add(ref)
                unique_refs.append(ref)

        return unique_refs
