from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import polars as pl
from pydantic import BaseModel, ConfigDict, Field

from semantic_finance_etl.domain.models.data_schema import DataSchema


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
    """Payload produced by a SourceReader.

    ``frame`` must be a Polars ``LazyFrame``.  Call ``collect()`` only when
    a downstream stage genuinely requires materialized data.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    asset: DiscoveredAsset
    frame: pl.LazyFrame
    data_schema: DataSchema | None = None
    parse_metadata: dict[str, Any] = Field(default_factory=dict)
    lineage_refs: list[str] = Field(default_factory=list)

    def with_frame(self, frame: pl.LazyFrame) -> "ReadPayload":
        return self.model_copy(update={"frame": frame})

    def with_schema(self, data_schema: DataSchema) -> "ReadPayload":
        return self.model_copy(update={"data_schema": data_schema})

    def collect(self) -> pl.DataFrame:
        """Explicit materialization boundary — call only when required."""
        return self.frame.collect()


class BatchPayload(BaseModel):
    """Payload produced after appending one or more ``ReadPayload`` frames.

    ``frame`` carries the combined lazy execution plan across all source reads.
    No hidden ``.collect()`` should occur between hook stages.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    table_name: str
    source_id: str | None = None
    frame: pl.LazyFrame | None = None
    data_schema: DataSchema | None = None
    assets: list[DiscoveredAsset] = Field(default_factory=list)
    combine_strategy: str | None = None
    lineage_refs: list[str] = Field(default_factory=list)
    batch_metadata: dict[str, Any] = Field(default_factory=dict)

    def with_frame(self, frame: pl.LazyFrame) -> "BatchPayload":
        return self.model_copy(update={"frame": frame})

    def with_schema(self, data_schema: DataSchema) -> "BatchPayload":
        return self.model_copy(update={"data_schema": data_schema})

    def collect(self) -> pl.DataFrame:
        """Explicit materialization boundary — call only when required."""
        if self.frame is None:
            return pl.DataFrame()
        return self.frame.collect()


class ValidatedBatchPayload(BaseModel):
    """Payload produced by the validation service.

    ``valid_frame`` and ``invalid_frame`` remain lazy until the load boundary.
    The load service is the designated ``collect()`` caller for ``valid_frame``.
    The DLQ service is the designated ``collect()`` caller for ``invalid_frame``.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    table_name: str
    valid_frame: pl.LazyFrame
    invalid_frame: pl.LazyFrame | None = None
    data_schema: DataSchema | None = None
    validation_summary: dict[str, Any] = Field(default_factory=dict)
    target_schema: dict[str, str] = Field(default_factory=dict)
    valid_row_count: int | None = None
    invalid_row_count: int | None = None
    lineage_refs: list[str] = Field(default_factory=list)

    def with_valid_frame(self, frame: pl.LazyFrame) -> "ValidatedBatchPayload":
        return self.model_copy(update={"valid_frame": frame})

    def with_invalid_frame(self, frame: pl.LazyFrame | None) -> "ValidatedBatchPayload":
        return self.model_copy(update={"invalid_frame": frame})

    def collect_valid(self) -> pl.DataFrame:
        """Explicit materialization boundary for load stage."""
        return self.valid_frame.collect()

    def collect_invalid(self) -> pl.DataFrame | None:
        """Explicit materialization boundary for DLQ stage."""
        if self.invalid_frame is None:
            return None
        return self.invalid_frame.collect()


class LoadPayload(BaseModel):
    """Payload passed to the load service.

    ``frame`` here is the **already-collected** ``pl.DataFrame``.  This is
    the one place in the pipeline where materialization is always required.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    table_name: str
    frame: pl.DataFrame
    load_mode: str
    primary_key_fields: list[str] = Field(default_factory=list)
    record_hash_enabled: bool = False
    load_metadata: dict[str, Any] = Field(default_factory=dict)
    lineage_refs: list[str] = Field(default_factory=list)


class DerivedBuildPayload(BaseModel):
    """Payload for derived table hooks.

    ``dependency_frames`` maps canonical table names to their ``LazyFrame``
    plans so derived hooks can join/aggregate lazily.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    table_name: str
    dependency_frames: dict[str, pl.LazyFrame] = Field(default_factory=dict)
    output_frame: pl.LazyFrame | None = None
    data_schema: DataSchema | None = None
    materialization_type: str = "table"
    build_metadata: dict[str, Any] = Field(default_factory=dict)
    lineage_refs: list[str] = Field(default_factory=list)

    def with_output_frame(self, frame: pl.LazyFrame) -> "DerivedBuildPayload":
        return self.model_copy(update={"output_frame": frame})

    def collect_output(self) -> pl.DataFrame:
        """Explicit materialization boundary for derived table load."""
        if self.output_frame is None:
            return pl.DataFrame()
        return self.output_frame.collect()


class SemanticProjectionPayload(BaseModel):
    """Payload for semantic hook stages.

    ``rows`` carries the source table data as a ``LazyFrame``.  Collect only
    at document generation or indexing boundaries.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    semantic_id: str
    source_table: str
    rows: pl.LazyFrame | None = None
    projection_template: dict[str, Any] = Field(default_factory=dict)
    chunking_config: dict[str, Any] = Field(default_factory=dict)
    semantic_metadata: dict[str, Any] = Field(default_factory=dict)
    lineage_refs: list[str] = Field(default_factory=list)

    def with_rows(self, rows: pl.LazyFrame) -> "SemanticProjectionPayload":
        return self.model_copy(update={"rows": rows})

    def collect_rows(self) -> pl.DataFrame | None:
        """Explicit materialization boundary for semantic projection."""
        if self.rows is None:
            return None
        return self.rows.collect()
