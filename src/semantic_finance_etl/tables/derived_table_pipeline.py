from __future__ import annotations

from dataclasses import dataclass, field

import polars as pl

from semantic_finance_etl.config.models.project_config import ProjectConfig
from semantic_finance_etl.config.models.table_config import TableConfig
from semantic_finance_etl.domain.enums.hook_stage import HookStage
from semantic_finance_etl.domain.models.hook_payloads import DerivedBuildPayload
from semantic_finance_etl.domain.models.runtime_table_definition import (
    RuntimeTableDefinition,
)
from semantic_finance_etl.etl.hooks.hook_binding_resolver import HookBindingResolver
from semantic_finance_etl.etl.hooks.hook_runner import HookRunSummary, HookRunner
from semantic_finance_etl.infrastructure.plugins.local_plugin_registry import (
    LocalPluginRegistry,
)


@dataclass(slots=True)
class DerivedTableResult:
    """Result of building one derived table."""

    run_id: str
    table_name: str
    rows_written: int = 0
    pre_derive_records: list[HookRunSummary] = field(default_factory=list)
    post_derive_records: list[HookRunSummary] = field(default_factory=list)
    error: str | None = None


class DerivedTablePipeline:
    """Builds a derived table from its canonical and derived dependencies.

    Execution model:
    - Dependency frames are loaded as ``pl.LazyFrame`` from SQLite
      (no data pulled until a hook or validation/load boundary collects).
    - ``pre_derive`` hooks receive a ``DerivedBuildPayload`` with
      ``dependency_frames`` and can reshape/filter lazily.
    - The hook that actually builds the derived output sets
      ``payload.output_frame`` as a ``pl.LazyFrame``.
    - ``post_derive`` hooks receive the built payload for post-processing.
    - Collection happens only at the load boundary inside this pipeline.
    """

    def __init__(
        self,
        *,
        hook_runner: HookRunner | None = None,
        hook_registry: LocalPluginRegistry | None = None,
        db_path: str,
    ) -> None:
        self._hook_runner = hook_runner or HookRunner()
        self._hook_registry = hook_registry or LocalPluginRegistry()
        self._db_path = db_path

    def run(
        self,
        *,
        project_config: ProjectConfig,
        table_config: TableConfig,
        runtime_table: RuntimeTableDefinition,
        run_id: str,
    ) -> DerivedTableResult:
        """Execute the full build pipeline for one derived table.

        Steps:
        1. Load dependency frames as lazy reads from SQLite.
        2. Run ``pre_derive`` hooks (shaping/filtering lazily).
        3. Build hook constructs ``output_frame`` as a ``pl.LazyFrame``.
        4. Run ``post_derive`` hooks.
        5. Collect ``output_frame`` and write to SQLite (load boundary).
        """
        result = DerivedTableResult(run_id=run_id, table_name=table_config.table_name)

        try:
            # Step 1 — Load dependency frames (lazy reads).
            dependency_frames = self._load_dependency_frames(
                table_config=table_config,
                project_config=project_config,
            )

            payload = DerivedBuildPayload(
                table_name=table_config.table_name,
                dependency_frames=dependency_frames,
                build_metadata={
                    "depends_on": list(table_config.depends_on),
                    "run_id": run_id,
                },
            )

            resolver = HookBindingResolver(self._hook_registry)

            # Step 2 — pre_derive hooks.
            if table_config.build and table_config.build.hooks.pre_derive:
                resolved = resolver.resolve_bindings_for_stage(
                    stage=HookStage.PRE_DERIVE,
                    bindings=table_config.build.hooks.pre_derive,
                )
                if resolved:
                    summary = self._hook_runner.run_stage(
                        project_config=project_config,
                        run_id=run_id,
                        stage=HookStage.PRE_DERIVE,
                        payload=payload,
                        bindings=resolved,
                        table_name=table_config.table_name,
                    )
                    payload = summary.final_payload
                    result.pre_derive_records.append(summary)

            # Step 3 — post_derive hooks (the actual build hook sets output_frame).
            if table_config.build and table_config.build.hooks.post_derive:
                resolved = resolver.resolve_bindings_for_stage(
                    stage=HookStage.POST_DERIVE,
                    bindings=table_config.build.hooks.post_derive,
                )
                if resolved:
                    summary = self._hook_runner.run_stage(
                        project_config=project_config,
                        run_id=run_id,
                        stage=HookStage.POST_DERIVE,
                        payload=payload,
                        bindings=resolved,
                        table_name=table_config.table_name,
                    )
                    payload = summary.final_payload
                    result.post_derive_records.append(summary)

            if payload.output_frame is None:
                result.error = (
                    f"Derived table '{table_config.table_name}' produced no output_frame. "
                    "A post_derive hook must set payload.output_frame."
                )
                return result

            # Step 4 — Collect + write (explicit materialization boundary).
            output_frame = payload.output_frame
            if output_frame is not None and table_config.load.record_hash:
                canonical_cols = [c.name for c in table_config.columns]
                present_cols = [c for c in canonical_cols if c in output_frame.collect_schema().names()]
                if present_cols:
                    import polars as pl
                    output_frame = output_frame.with_columns(
                        pl.concat_str(
                            [pl.col(c).cast(pl.Utf8).fill_null("") for c in present_cols],
                            separator="||"
                        ).hash(seed=42).cast(pl.Utf8).alias("_record_hash")
                    )

            rows_written = self._write_output(
                output_frame=output_frame,
                runtime_table=runtime_table,
            )
            result.rows_written = rows_written

        except Exception as exc:
            result.error = f"{type(exc).__name__}: {exc}"

        return result

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _load_dependency_frames(
        self,
        table_config: TableConfig,
        project_config: ProjectConfig,
    ) -> dict[str, pl.LazyFrame]:
        """Read each dependency table from SQLite as a ``pl.LazyFrame``."""
        import sqlite3

        frames: dict[str, pl.LazyFrame] = {}
        db_path = project_config.runtime.local_db_path

        for dep_name in table_config.depends_on:
            try:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                try:
                    cursor = conn.cursor()
                    cursor.execute(f"SELECT * FROM {dep_name}")  # noqa: S608
                    rows = cursor.fetchall()
                    col_names = [d[0] for d in cursor.description or []]
                finally:
                    conn.close()

                if rows:
                    df = pl.DataFrame([dict(r) for r in rows], infer_schema_length=1000)
                else:
                    df = pl.DataFrame({col: [] for col in col_names})

                frames[dep_name] = df.lazy()
            except Exception as exc:
                raise RuntimeError(
                    f"Failed to load dependency table '{dep_name}' for derived table "
                    f"'{table_config.table_name}': {exc}"
                ) from exc

        return frames

    def _write_output(
        self,
        output_frame: pl.LazyFrame,
        runtime_table: RuntimeTableDefinition,
    ) -> int:
        """Collect the output frame and write to SQLite — the load boundary."""
        from semantic_finance_etl.infrastructure.database.sqlite_writer import (
            SQLiteWriter,
        )

        df = output_frame.collect()
        writer = SQLiteWriter(self._db_path)

        writer.write_dataframe(
            runtime_table=runtime_table,
            df=df,
            mode=runtime_table.load_mode,
        )
        return len(df)
