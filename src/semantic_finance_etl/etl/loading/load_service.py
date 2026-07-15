from __future__ import annotations

from semantic_finance_etl.config.models.runtime_config import RuntimeConfig
from semantic_finance_etl.domain.models.hook_payloads import (
    LoadPayload,
    ValidatedBatchPayload,
)
from semantic_finance_etl.domain.models.runtime_table_definition import (
    RuntimeTableDefinition,
)
from semantic_finance_etl.infrastructure.database.sqlite_writer import SQLiteWriter


class LoadService:
    def __init__(self, runtime_config: RuntimeConfig) -> None:
        self._runtime_config = runtime_config
        self._writer = SQLiteWriter(runtime_config.local_db_path)

    def prepare_load_payload(
        self,
        validated_payload: ValidatedBatchPayload,
        runtime_table: RuntimeTableDefinition,
    ) -> LoadPayload:
        return LoadPayload(
            table_name=validated_payload.table_name,
            frame=validated_payload.frame,
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
    ) -> dict:
        frame = validated_payload.frame

        if frame is None:
            frame = []

        if not isinstance(frame, list):
            raise ValueError(
                "LoadService currently expects validated frame to be list[dict[str, object]]."
            )

        return self._writer.write_rows(
            runtime_table=runtime_table,
            rows=frame,
            mode=runtime_table.load_mode,
        )
