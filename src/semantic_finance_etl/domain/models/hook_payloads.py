from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ExecutionContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    run_id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    table_name: str | None = None
    source_id: str | None = None
    stage: str | None = None
    started_at_utc: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class DiscoveredAsset(BaseModel):
    path: str
    source_id: str
    size_bytes: int | None = None
    modified_at_utc: datetime | None = None
    created_at_utc: datetime | None = None
    content_hash: str | None = None
    extra_metadata: dict[str, Any] = Field(default_factory=dict)


class DiscoveryPayload(BaseModel):
    assets: list[DiscoveredAsset] = Field(default_factory=list)
    source_config_snapshot: dict[str, Any] = Field(default_factory=dict)
    discovery_metadata: dict[str, Any] = Field(default_factory=dict)


class ReadPayload(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    asset: DiscoveredAsset
    frame: Any
    inferred_schema: dict[str, str] = Field(default_factory=dict)
    parse_metadata: dict[str, Any] = Field(default_factory=dict)
    lineage_refs: list[str] = Field(default_factory=list)

    def with_frame(self, frame: Any) -> "ReadPayload":
        return self.model_copy(update={"frame": frame})


class BatchPayload(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    table_name: str
    source_id: str | None = None
    frame: Any = None
    assets: list[DiscoveredAsset] = Field(default_factory=list)
    combine_strategy: str | None = None
    inferred_schema: dict[str, str] = Field(default_factory=dict)
    lineage_refs: list[str] = Field(default_factory=list)
    batch_metadata: dict[str, Any] = Field(default_factory=dict)

    def with_frame(self, frame: Any) -> "BatchPayload":
        return self.model_copy(update={"frame": frame})


class ValidatedBatchPayload(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    table_name: str
    frame: Any
    validation_summary: dict[str, Any] = Field(default_factory=dict)
    target_schema: dict[str, str] = Field(default_factory=dict)
    valid_row_count: int | None = None
    invalid_row_count: int | None = None
    lineage_refs: list[str] = Field(default_factory=list)

    def with_frame(self, frame: Any) -> "ValidatedBatchPayload":
        return self.model_copy(update={"frame": frame})


class LoadPayload(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    table_name: str
    frame: Any
    load_mode: str
    primary_key_fields: list[str] = Field(default_factory=list)
    record_hash_enabled: bool = False
    load_metadata: dict[str, Any] = Field(default_factory=dict)
    lineage_refs: list[str] = Field(default_factory=list)

    def with_frame(self, frame: Any) -> "LoadPayload":
        return self.model_copy(update={"frame": frame})


class DerivedBuildPayload(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    table_name: str
    dependency_frames: dict[str, Any] = Field(default_factory=dict)
    materialization_type: str = "table"
    build_metadata: dict[str, Any] = Field(default_factory=dict)
    lineage_refs: list[str] = Field(default_factory=list)

    def with_dependency_frames(
        self,
        dependency_frames: dict[str, Any],
    ) -> "DerivedBuildPayload":
        return self.model_copy(update={"dependency_frames": dependency_frames})


class SemanticProjectionPayload(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    semantic_id: str
    source_table: str
    rows: Any = None
    projection_template: dict[str, Any] = Field(default_factory=dict)
    chunking_config: dict[str, Any] = Field(default_factory=dict)
    semantic_metadata: dict[str, Any] = Field(default_factory=dict)
    lineage_refs: list[str] = Field(default_factory=list)

    def with_rows(self, rows: Any) -> "SemanticProjectionPayload":
        return self.model_copy(update={"rows": rows})
