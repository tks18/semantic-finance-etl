from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator

from semantic_finance_etl.config.models.transform_config import StageHookBindings
from semantic_finance_etl.domain.enums.load_mode import LoadMode
from semantic_finance_etl.domain.enums.table_kind import TableKind


class ColumnConfig(BaseModel):
    name: str
    type: str
    nullable: bool = True
    description: str | None = None
    default: Any | None = None
    primary_key_part: bool = False
    indexed: bool = False


class PrimaryKeyStrategyConfig(BaseModel):
    type: str
    fields: list[str] = Field(default_factory=list)


class ForeignKeyConfig(BaseModel):
    columns: list[str]
    target_table: str
    target_columns: list[str]


class LoadConfig(BaseModel):
    mode: LoadMode = LoadMode.APPEND
    record_hash: bool = False
    deduplicate_before_load: bool = False


class BuildConfig(BaseModel):
    strategy: str = "python_hook"
    hooks: StageHookBindings = Field(default_factory=StageHookBindings)


class TableConfig(BaseModel):
    table_name: str
    table_kind: TableKind = TableKind.CANONICAL
    description: str | None = None

    columns: list[ColumnConfig] = Field(default_factory=list)
    primary_key_strategy: PrimaryKeyStrategyConfig | None = None
    foreign_keys: list[ForeignKeyConfig] = Field(default_factory=list)
    hooks: StageHookBindings = Field(default_factory=StageHookBindings)
    load: LoadConfig = Field(default_factory=LoadConfig)

    depends_on: list[str] = Field(default_factory=list)
    build: BuildConfig | None = None

    @model_validator(mode="after")
    def validate_table(self) -> "TableConfig":
        column_names = [column.name for column in self.columns]
        if len(column_names) != len(set(column_names)):
            raise ValueError(f"Duplicate column names found in table '{self.table_name}'.")

        if self.table_kind == TableKind.DERIVED and not self.depends_on:
            raise ValueError(
                f"Derived table '{self.table_name}' must define 'depends_on'."
            )

        if self.table_kind == TableKind.DERIVED and self.build is None:
            raise ValueError(
                f"Derived table '{self.table_name}' must define 'build'."
            )

        return self
