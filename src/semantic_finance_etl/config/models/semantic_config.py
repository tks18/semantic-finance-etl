from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from semantic_finance_etl.config.models.transform_config import StageHookBindings


class ProjectionConfig(BaseModel):
    title_template: str | None = None
    body_template: str
    metadata_fields: list[str] = Field(default_factory=list)
    tag_fields: list[str] = Field(default_factory=list)


class ChunkingConfig(BaseModel):
    chunk_size: int = 1000
    chunk_overlap: int = 100


class SemanticConfig(BaseModel):
    semantic_id: str
    source_table: str
    document_id_strategy: str = "deterministic_hash"

    projection: ProjectionConfig
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)

    hooks: StageHookBindings = Field(default_factory=StageHookBindings)
    extra_metadata: dict[str, Any] = Field(default_factory=dict)
