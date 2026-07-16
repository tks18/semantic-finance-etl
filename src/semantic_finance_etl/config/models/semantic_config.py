from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from semantic_finance_etl.config.models.transform_config import StageHookBindings

class SemanticTemplateConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    table_name: str
    enabled: bool = True
    body_template: str
    metadata_fields: list[str] = Field(default_factory=list)
    tag_fields: list[str] = Field(default_factory=list)


class ProjectionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title_template: str | None = None
    body_template: str
    metadata_fields: list[str] = Field(default_factory=list)
    tag_fields: list[str] = Field(default_factory=list)


class ChunkingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    chunk_size: int = 1000
    chunk_overlap: int = 100

    @model_validator(mode='after')
    def validate_bounds(self) -> 'ChunkingConfig':
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if self.chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be strictly less than chunk_size")
        return self


class SemanticConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    semantic_id: str
    source_table: str
    source_pk_field: str | None = None
    document_id_strategy: str = "deterministic_hash"

    projection: ProjectionConfig
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)

    hooks: StageHookBindings = Field(default_factory=StageHookBindings)
    extra_metadata: dict[str, Any] = Field(default_factory=dict)
