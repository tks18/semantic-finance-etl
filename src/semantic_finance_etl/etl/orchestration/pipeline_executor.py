from __future__ import annotations

import sqlite3
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

import polars as pl

from semantic_finance_etl.config.models.project_config import ProjectConfig
from semantic_finance_etl.config.services.project_config_service import (
    ProjectConfigService,
)
from semantic_finance_etl.domain.enums.table_kind import TableKind
from semantic_finance_etl.domain.models.runtime_table_definition import (
    RuntimeTableDefinition,
)
from semantic_finance_etl.etl.dlq.dlq_service import DLQService, DLQSummary
from semantic_finance_etl.etl.lineage.lineage_service import LineageService
from semantic_finance_etl.etl.loading.load_service import LoadResult, LoadService
from semantic_finance_etl.etl.orchestration.dag_builder import DAGBuilder
from semantic_finance_etl.etl.tracking.run_tracking_service import (
    RunSummary,
    RunTrackingService,
)
from semantic_finance_etl.etl.validation.validation_service import ValidationService
from semantic_finance_etl.infrastructure.plugins.local_plugin_registry import (
    LocalPluginRegistry,
)
from semantic_finance_etl.semantic.chunking_service import ChunkingService
from semantic_finance_etl.semantic.indexing_service import IndexingResult, IndexingService
from semantic_finance_etl.semantic.projection_service import ProjectionService
from semantic_finance_etl.tables.configured_table_pipeline import (
    ConfiguredTablePipeline,
    TablePipelineExecutionResult,
)
from semantic_finance_etl.tables.derived_table_pipeline import (
    DerivedTablePipeline,
    DerivedTableResult,
)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class TableRunResult:
    """Result of running one canonical source → table pipeline."""

    run_id: str
    source_id: str
    table_name: str
    pipeline_result: TablePipelineExecutionResult
    load_result: LoadResult | None = None
    dlq_summary: DLQSummary | None = None
    schema_issues: list[dict] = field(default_factory=list)
    error: str | None = None


@dataclass(slots=True)
class SemanticRunResult:
    """Result of running one semantic projection + indexing pass."""

    semantic_id: str
    source_table: str
    documents_projected: int = 0
    chunks_produced: int = 0
    indexing_result: IndexingResult | None = None
    error: str | None = None


@dataclass(slots=True)
class PipelineExecutionSummary:
    run_id: str
    project_id: str
    canonical_results: list[TableRunResult] = field(default_factory=list)
    derived_results: list[DerivedTableResult] = field(default_factory=list)
    semantic_results: list[SemanticRunResult] = field(default_factory=list)
    error: str | None = None

    @property
    def total_rows_loaded(self) -> int:
        return sum(
            (r.load_result.inserted_rows + r.load_result.updated_rows)
            for r in self.canonical_results
            if r.load_result is not None
        )

    @property
    def total_rows_invalid(self) -> int:
        return sum(
            r.dlq_summary.persisted_row_count
            for r in self.canonical_results
            if r.dlq_summary is not None
        )

    @property
    def total_chunks_indexed(self) -> int:
        return sum(
            r.indexing_result.indexed_chunks
            for r in self.semantic_results
            if r.indexing_result is not None
        )


# ---------------------------------------------------------------------------
# Executor
# ---------------------------------------------------------------------------


class PipelineExecutor:
    """Top-level ETL run coordinator.

    Execution order per run:
    1. Register hooks.
    2. Canonical tables: discover → read → transform (lazy) → validate → DLQ → load.
    3. Derived tables: topological order (DAG) → pre/post_derive hooks → collect → write.
    4. Semantic layer: project → chunk → index.
    5. Record run tracking start / complete / fail.
    """

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

    def run(self, config_root: str | Path) -> PipelineExecutionSummary:
        project_config = self._config_service.load(config_root)
        run_id = str(uuid4())
        project_id = project_config.project.project_id
        db_path = project_config.runtime.local_db_path

        from semantic_finance_etl.utils.logging_setup import setup_logging
        import logging
        setup_logging(
            log_level=project_config.runtime.log_level,
            log_dir=project_config.runtime.log_dir
        )
        logger = logging.getLogger("semantic_finance_etl.executor")
        logger.info(f"Starting pipeline execution. Run ID: {run_id}, Project ID: {project_id}")

        # Shared services
        run_tracker = RunTrackingService(db_path)
        lineage_service = LineageService(db_path)
        dlq_service = DLQService(db_path)
        validation_service = ValidationService()
        load_service = LoadService(project_config.runtime)
        projection_service = ProjectionService()
        chunking_service = ChunkingService()
        indexing_service = IndexingService(db_path)

        run_tracker.start_run(run_id=run_id, project_id=project_id)

        canonical_results: list[TableRunResult] = []
        derived_results: list[DerivedTableResult] = []
        semantic_results: list[SemanticRunResult] = []

        try:
            self._hook_registry.register_from_search_paths(
                project_config.runtime.hook_search_paths
            )

            canonical_pipeline = self._configured_table_pipeline or ConfiguredTablePipeline(
                hook_registry=self._hook_registry
            )
            derived_pipeline = DerivedTablePipeline(
                hook_registry=self._hook_registry,
                db_path=db_path,
            )
            
            tables_by_name = {t.table_name: t for t in project_config.tables}
            # ----------------------------------------------------------------
            # Phase 1 — Canonical tables
            # ----------------------------------------------------------------
            for source in project_config.sources:
                for target_table_name in source.target_tables:
                    table_config = tables_by_name[target_table_name]
                    if table_config.table_kind != TableKind.CANONICAL:
                        continue

                    runtime_table = RuntimeTableDefinition.from_table_config(table_config)
                    result = self._run_canonical_table(
                        run_id=run_id,
                        project_config=project_config,
                        source_config=source,
                        table_config=table_config,
                        runtime_table=runtime_table,
                        pipeline=canonical_pipeline,
                        validation_service=validation_service,
                        load_service=load_service,
                        dlq_service=dlq_service,
                        lineage_service=lineage_service,
                    )
                    canonical_results.append(result)

            # ----------------------------------------------------------------
            # Phase 2 — Derived tables (DAG order)
            # ----------------------------------------------------------------
            build_plan = DAGBuilder().build(project_config.tables)

            for derived_table_name in build_plan.derived_tables:
                table_config = tables_by_name[derived_table_name]
                runtime_table = RuntimeTableDefinition.from_table_config(table_config)

                result = derived_pipeline.run(
                    project_config=project_config,
                    table_config=table_config,
                    runtime_table=runtime_table,
                    run_id=run_id,
                )
                derived_results.append(result)

                lineage_service.record_output_lineage(
                    run_id=run_id,
                    table_name=derived_table_name,
                    output_ref=derived_table_name,
                    stage="derive",
                )

            # ----------------------------------------------------------------
            # Phase 3 — Semantic layer
            # ----------------------------------------------------------------
            for semantic_config in project_config.semantics:
                sem_result = self._run_semantic(
                    run_id=run_id,
                    db_path=db_path,
                    semantic_config=semantic_config,
                    projection_service=projection_service,
                    chunking_service=chunking_service,
                    indexing_service=indexing_service,
                    lineage_service=lineage_service,
                )
                semantic_results.append(sem_result)

        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
            run_tracker.fail_run(run_id=run_id, error=error_msg)
            return PipelineExecutionSummary(
                run_id=run_id,
                project_id=project_id,
                canonical_results=canonical_results,
                derived_results=derived_results,
                semantic_results=semantic_results,
                error=error_msg,
            )

        summary = PipelineExecutionSummary(
            run_id=run_id,
            project_id=project_id,
            canonical_results=canonical_results,
            derived_results=derived_results,
            semantic_results=semantic_results,
        )

        has_errors = (
            any(r.error for r in canonical_results)
            or any(r.error for r in derived_results)
            or any(r.error for r in semantic_results)
        )

        if has_errors:
            error_msg = "Pipeline completed with child errors."
            run_tracker.fail_run(run_id=run_id, error=error_msg)
            summary.error = error_msg
        else:
            run_tracker.complete_run(
                run_id=run_id,
                summary=RunSummary(
                    source_count=len(project_config.sources),
                    table_count=len(canonical_results) + len(derived_results),
                    total_rows_loaded=summary.total_rows_loaded,
                    total_rows_invalid=summary.total_rows_invalid,
                ),
            )

        return summary

    # ------------------------------------------------------------------
    # Private — canonical table run
    # ------------------------------------------------------------------

    def _run_canonical_table(
        self,
        *,
        run_id: str,
        project_config: ProjectConfig,
        source_config,
        table_config,
        runtime_table: RuntimeTableDefinition,
        pipeline: ConfiguredTablePipeline,
        validation_service: ValidationService,
        load_service: LoadService,
        dlq_service: DLQService,
        lineage_service: LineageService,
    ) -> TableRunResult:
        try:
            pipeline_result = pipeline.run(
                project_config=project_config,
                source_config=source_config,
                table_config=table_config,
                run_id=run_id,
            )

            for asset in (
                pipeline_result.final_batch_payload.assets
                if pipeline_result.final_batch_payload
                else []
            ):
                lineage_service.record_file_lineage(
                    run_id=run_id,
                    source_path=asset.path,
                    table_name=table_config.table_name,
                )

            if pipeline_result.final_batch_payload is None:
                return TableRunResult(
                    run_id=run_id,
                    source_id=source_config.source_id,
                    table_name=table_config.table_name,
                    pipeline_result=pipeline_result,
                    error="Pipeline produced no batch payload.",
                )

            batch_payload = pipeline_result.final_batch_payload

            # Schema validation (lazy — no collect)
            schema_result = validation_service.validate_schema(
                batch_payload=batch_payload,
                runtime_table=runtime_table,
            )
            schema_issues = [
                {"column": i.column, "reason": i.reason, "severity": i.severity}
                for i in schema_result.issues
            ]

            if not schema_result.is_valid:
                return TableRunResult(
                    run_id=run_id,
                    source_id=source_config.source_id,
                    table_name=table_config.table_name,
                    pipeline_result=pipeline_result,
                    schema_issues=schema_issues,
                    error="Schema validation failed: "
                    + "; ".join(i.reason for i in schema_result.error_issues),
                )

            # Data validation (collects inside ValidationService)
            validated_payload = validation_service.validate_batch(
                batch_payload=batch_payload,
                runtime_table=runtime_table,
            )

            # DLQ (collects invalid_frame inside DLQService)
            dlq_summary = dlq_service.persist_invalid_rows(
                invalid_frame=validated_payload.invalid_frame,
                stage="validation",
                source_id=source_config.source_id,
                table_name=table_config.table_name,
                run_id=run_id,
            )

            # Load (collects valid_frame inside LoadService)
            load_result = load_service.load(
                validated_payload=validated_payload,
                runtime_table=runtime_table,
            )

            lineage_service.record_output_lineage(
                run_id=run_id,
                table_name=table_config.table_name,
                output_ref=runtime_table.table_name,
            )

            return TableRunResult(
                run_id=run_id,
                source_id=source_config.source_id,
                table_name=table_config.table_name,
                pipeline_result=pipeline_result,
                load_result=load_result,
                dlq_summary=dlq_summary,
                schema_issues=schema_issues,
            )

        except Exception as exc:
            return TableRunResult(
                run_id=run_id,
                source_id=source_config.source_id,
                table_name=table_config.table_name,
                pipeline_result=TablePipelineExecutionResult(
                    run_id=run_id,
                    source_id=source_config.source_id,
                    table_name=table_config.table_name,
                ),
                error=f"{type(exc).__name__}: {exc}",
            )

    # ------------------------------------------------------------------
    # Private — semantic run
    # ------------------------------------------------------------------

    def _run_semantic(
        self,
        *,
        run_id: str,
        db_path: str,
        semantic_config,
        projection_service: ProjectionService,
        chunking_service: ChunkingService,
        indexing_service: IndexingService,
        lineage_service: LineageService,
    ) -> SemanticRunResult:
        result = SemanticRunResult(
            semantic_id=semantic_config.semantic_id,
            source_table=semantic_config.source_table,
        )

        try:
            # Load source table as a LazyFrame.
            lazy_frame = self._load_table_as_lazy(
                db_path=db_path,
                table_name=semantic_config.source_table,
            )

            # Project (collects inside ProjectionService).
            projection_result = projection_service.project(
                lazy_frame=lazy_frame,
                semantic_config=semantic_config,
            )
            result.documents_projected = projection_result.document_count

            if not projection_result.documents:
                result.error = "No documents projected — source table may be empty."
                return result

            # Chunk (pure CPU — no I/O).
            chunking_result = chunking_service.chunk_documents(
                documents=projection_result.documents,
                chunking_config=semantic_config.chunking,
            )
            result.chunks_produced = chunking_result.total_chunks

            # Index.
            indexing_result = indexing_service.index_chunks(
                chunks=chunking_result.chunks,
                run_id=run_id,
            )
            result.indexing_result = indexing_result

            lineage_service.record_output_lineage(
                run_id=run_id,
                table_name=semantic_config.source_table,
                output_ref=f"semantic::{semantic_config.semantic_id}",
                stage="semantic",
            )

        except Exception as exc:
            result.error = f"{type(exc).__name__}: {exc}"

        return result

    def _load_table_as_lazy(self, *, db_path: str, table_name: str) -> pl.LazyFrame:
        """Read a SQLite table into a Polars LazyFrame for semantic projection."""
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name}")  # noqa: S608
            rows = cursor.fetchall()
            col_names = [d[0] for d in cursor.description or []]
        finally:
            conn.close()

        if rows:
            df = pl.DataFrame([dict(r) for r in rows], infer_schema_length=1000)
        else:
            df = pl.DataFrame({col: [] for col in col_names})

        return df.lazy()
