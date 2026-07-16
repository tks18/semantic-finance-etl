from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from semantic_finance_etl.config.models.runtime_config import RuntimeConfig
from semantic_finance_etl.config.models.semantic_config import SemanticConfig
from semantic_finance_etl.config.models.source_config import SourceConfig
from semantic_finance_etl.config.models.table_config import TableConfig


class ProjectMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: str
    name: str
    description: str | None = None
    version: str = "0.1.0"


class ProjectConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project: ProjectMetadata
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)

    sources: list[SourceConfig] = Field(default_factory=list)
    tables: list[TableConfig] = Field(default_factory=list)
    semantics: list[SemanticConfig] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_project(self) -> "ProjectConfig":
        source_ids = [source.source_id for source in self.sources]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("Duplicate source_id values found in project config.")

        table_names = [table.table_name for table in self.tables]
        if len(table_names) != len(set(table_names)):
            raise ValueError("Duplicate table_name values found in project config.")

        semantic_ids = [semantic.semantic_id for semantic in self.semantics]
        if len(semantic_ids) != len(set(semantic_ids)):
            raise ValueError("Duplicate semantic_id values found in project config.")

        table_name_set = set(table_names)

        for source in self.sources:
            for target_table in source.target_tables:
                if target_table not in table_name_set:
                    raise ValueError(
                        f"Source '{source.source_id}' references missing target table '{target_table}'."
                    )

        for semantic in self.semantics:
            if semantic.source_table not in table_name_set:
                raise ValueError(
                    f"Semantic config '{semantic.semantic_id}' references missing source table "
                    f"'{semantic.source_table}'."
                )

        for table in self.tables:
            for dependency in table.depends_on:
                if dependency not in table_name_set:
                    raise ValueError(
                        f"Table '{table.table_name}' depends on missing table '{dependency}'."
                    )

        return self
