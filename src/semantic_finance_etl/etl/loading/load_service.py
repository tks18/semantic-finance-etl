from __future__ import annotations

from dataclasses import dataclass

import polars as pl

from semantic_finance_etl.config.models.runtime_config import RuntimeConfig
from semantic_finance_etl.domain.models.hook_payloads import (
    LoadPayload,
    ValidatedBatchPayload,
)
from semantic_finance_etl.domain.models.runtime_table_definition import (
    RuntimeTableDefinition,
)
from semantic_finance_etl.infrastructure.database.sqlite_writer import SQLiteWriter


@dataclass(slots=True)
class LoadResult:
    """Structured result from a single table load operation."""

    table_name: str
    mode: str
    inserted_rows: int
    updated_rows: int
    total_affected: int


class LoadService:
    """Bridges validated payloads to the SQLite writer.

    This service owns the **final collect boundary**: it calls
    ``ValidatedBatchPayload.collect_valid()`` here, then passes the
    materialized ``pl.DataFrame`` to the writer.  No caller above this
    service should need to call ``.collect()`` on a valid frame.
    """

    def __init__(self, runtime_config: RuntimeConfig) -> None:
        self._runtime_config = runtime_config
        self._writer = SQLiteWriter(runtime_config.local_db_path)

    def prepare_load_payload(
        self,
        validated_payload: ValidatedBatchPayload,
        runtime_table: RuntimeTableDefinition,
    ) -> LoadPayload:
        """Collect the valid frame and build a ``LoadPayload``.

        This is the designated ``collect()`` boundary for the load stage.
        """
        df: pl.DataFrame = validated_payload.collect_valid()

        return LoadPayload(
            table_name=validated_payload.table_name,
            frame=df,
            load_mode=runtime_table.load_mode,
            primary_key_fields=runtime_table.primary_key_fields,
            record_hash_enabled=runtime_table.record_hash_enabled,
            load_metadata={
                "valid_row_count": validated_payload.valid_row_count,
                "invalid_row_count": validated_payload.invalid_row_count,
            },
            lineage_refs=validated_payload.lineage_refs,
        )

    def load(
        self,
        validated_payload: ValidatedBatchPayload,
        runtime_table: RuntimeTableDefinition,
    ) -> LoadResult:
        """Load valid rows from the validated payload into SQLite.

        Collects the valid frame here (single explicit boundary), then
        delegates to the SQLite writer with the materialized DataFrame.
        """
        df: pl.DataFrame = validated_payload.collect_valid()

        write_summary = self._writer.write_dataframe(
            runtime_table=runtime_table,
            df=df,
            mode=runtime_table.load_mode,
        )

        return LoadResult(
            table_name=validated_payload.table_name,
            mode=runtime_table.load_mode,
            inserted_rows=write_summary.get("inserted_rows", 0),
            updated_rows=write_summary.get("updated_rows", 0),
            total_affected=write_summary.get("inserted_rows", 0)
            + write_summary.get("updated_rows", 0),
        )
