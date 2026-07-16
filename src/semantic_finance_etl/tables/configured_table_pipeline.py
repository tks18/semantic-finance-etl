from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

import polars as pl

from semantic_finance_etl.config.models.project_config import ProjectConfig
from semantic_finance_etl.config.models.source_config import SourceConfig
from semantic_finance_etl.config.models.table_config import TableConfig
from semantic_finance_etl.domain.enums.hook_stage import HookStage
from semantic_finance_etl.domain.models.data_schema import DataSchema
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

    post_read_records: list[HookRunSummary] = field(default_factory=list)
    post_append_records: list[HookRunSummary] = field(default_factory=list)
    pre_load_records: list[HookRunSummary] = field(default_factory=list)


class ConfiguredTablePipeline:
    """Orchestrates the ingestion pipeline for one source → one target table.

    Execution model:
    - All frames remain as ``pl.LazyFrame`` throughout hook stages.
    - Concatenation uses ``pl.concat([...], how="vertical_relaxed")`` — lazy,
      schema-harmonized, no premature collection.
    - ``.collect()`` is never called here; that is the validation or load
      service's responsibility.
    """

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
                    result.post_read_records.append(post_read_summary)

                read_payloads.append(read_payload)

        result.read_payload_count = len(read_payloads)

        # --- Lazy concatenation boundary ---
        # Concatenate all read frames into a single lazy plan.  No collection
        # occurs here.  Schema is merged from available DataSchema objects.
        combined_frame = self._concat_lazy_frames(read_payloads)
        merged_schema = self._merge_schemas(read_payloads)
        all_lineage_refs = self._collect_lineage_refs(read_payloads)

        if combined_frame is not None and table_config.load.record_hash:
            canonical_cols = [c.name for c in table_config.columns]
            # Get actual columns present in the schema to safely hash
            present_cols = [c for c in canonical_cols if c in combined_frame.collect_schema().names()]
            if present_cols:
                combined_frame = combined_frame.with_columns(
                    pl.concat_str(
                        [pl.col(c).cast(pl.Utf8).fill_null("") for c in present_cols],
                        separator="||"
                    ).hash(seed=42).cast(pl.Utf8).alias("_record_hash")
                )

        batch_payload = BatchPayload(
            table_name=table_config.table_name,
            source_id=source_config.source_id,
            frame=combined_frame,
            data_schema=merged_schema,
            assets=[payload.asset for payload in read_payloads],
            combine_strategy="lazy_vertical_relaxed",
            lineage_refs=all_lineage_refs,
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
            result.post_append_records.append(post_append_summary)

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
            result.pre_load_records.append(pre_load_summary)

        result.final_batch_payload = batch_payload
        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _concat_lazy_frames(
        self,
        read_payloads: list[ReadPayload],
    ) -> pl.LazyFrame | None:
        """Return a single lazy concatenated frame or ``None`` when empty.

        Uses ``how="vertical_relaxed"`` so minor schema differences between
        source files are tolerated (missing columns become nulls).
        No ``.collect()`` is called.
        """
        frames = []
        for p in read_payloads:
            if p.frame is not None:
                # Inject provenance columns lazily
                file_hash = p.asset.content_hash or "unknown"
                source_file = p.asset.path or "unknown"
                
                df = p.frame.with_columns([
                    pl.lit(file_hash).cast(pl.Utf8).alias("_file_hash"),
                    pl.lit(source_file).cast(pl.Utf8).alias("_source_file")
                ])
                frames.append(df)

        if not frames:
            return None

        if len(frames) == 1:
            return frames[0]

        return pl.concat(frames, how="vertical_relaxed")

    def _merge_schemas(
        self,
        read_payloads: list[ReadPayload],
    ) -> DataSchema | None:
        """Return the first non-None ``DataSchema`` found across payloads.

        Full schema merging (union of columns) can be added later.
        For now the first schema serves as the authoritative baseline.
        """
        for payload in read_payloads:
            if payload.data_schema is not None:
                return payload.data_schema
        return None

    def _collect_lineage_refs(
        self,
        read_payloads: list[ReadPayload],
    ) -> list[str]:
        """Collect all lineage refs, preserving order and removing duplicates."""
        seen: set[str] = set()
        unique_refs: list[str] = []

        for payload in read_payloads:
            for ref in payload.lineage_refs:
                if ref not in seen:
                    seen.add(ref)
                    unique_refs.append(ref)

        return unique_refs
