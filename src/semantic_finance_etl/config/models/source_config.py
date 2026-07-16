from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from semantic_finance_etl.config.models.transform_config import StageHookBindings


class ReaderConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str
    sql: str | None = None
    sheet_name: str | None = None
    header_row: int | None = None
    delimiter: str | None = None
    encoding: str | None = None


class SourceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_id: str
    description: str | None = None

    discoverer: str
    path: str
    recursive: bool = False
    include_patterns: list[str] = Field(default_factory=list)
    exclude_patterns: list[str] = Field(default_factory=list)

    selector: str = "all_files"
    selector_params: dict[str, Any] = Field(default_factory=dict)

    grouper: str = "single_group"
    grouper_params: dict[str, Any] = Field(default_factory=dict)

    reader: ReaderConfig
    target_tables: list[str] = Field(default_factory=list)

    hooks: StageHookBindings = Field(default_factory=StageHookBindings)

    @model_validator(mode="after")
    def validate_source(self) -> "SourceConfig":
        if not self.target_tables:
            raise ValueError(f"Source '{self.source_id}' must define at least one target table.")

        if not self.path.strip():
            raise ValueError(f"Source '{self.source_id}' must define a non-empty path.")

        return self
