from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from semantic_finance_etl.config.models.table_config import ColumnConfig, TableConfig


@dataclass(slots=True)
class RuntimeColumnDefinition:
    name: str
    type_name: str
    nullable: bool = True
    description: str | None = None
    default: Any | None = None
    primary_key_part: bool = False
    indexed: bool = False


@dataclass(slots=True)
class RuntimeForeignKeyDefinition:
    columns: list[str]
    target_table: str
    target_columns: list[str]


@dataclass(slots=True)
class RuntimeTableDefinition:
    table_name: str
    table_kind: str
    columns: list[RuntimeColumnDefinition] = field(default_factory=list)
    primary_key_fields: list[str] = field(default_factory=list)
    foreign_keys: list[RuntimeForeignKeyDefinition] = field(default_factory=list)
    load_mode: str = "append"
    record_hash_enabled: bool = False

    @property
    def columns_by_name(self) -> dict[str, RuntimeColumnDefinition]:
        return {column.name: column for column in self.columns}

    @property
    def column_names(self) -> list[str]:
        return [column.name for column in self.columns]

    @classmethod
    def from_table_config(cls, table_config: TableConfig) -> "RuntimeTableDefinition":
        columns = [
            RuntimeColumnDefinition(
                name=column.name,
                type_name=column.type,
                nullable=column.nullable,
                description=column.description,
                default=column.default,
                primary_key_part=column.primary_key_part,
                indexed=column.indexed,
            )
            for column in table_config.columns
        ]
        
        from semantic_finance_etl.domain.enums.table_kind import TableKind
        
        existing_cols = {c.name for c in columns}
        sys_cols_to_add = []
        
        if table_config.table_kind == TableKind.CANONICAL:
            sys_cols_to_add.extend([
                RuntimeColumnDefinition(name="_file_hash", type_name="str", nullable=True),
                RuntimeColumnDefinition(name="_source_file", type_name="str", nullable=True)
            ])
        
        if table_config.load.record_hash:
            sys_cols_to_add.append(
                RuntimeColumnDefinition(name="_record_hash", type_name="str", nullable=True)
            )
            
        for sys_col in sys_cols_to_add:
            if sys_col.name in existing_cols:
                raise ValueError(f"User column '{sys_col.name}' collides with system column in table '{table_config.table_name}'")
            columns.append(sys_col)
            
        primary_key_fields: list[str] = []

        if table_config.primary_key_strategy is not None:
            primary_key_fields = list(table_config.primary_key_strategy.fields)
        else:
            primary_key_fields = [
                column.name for column in columns if column.primary_key_part
            ]

        foreign_keys = [
            RuntimeForeignKeyDefinition(
                columns=list(fk.columns),
                target_table=fk.target_table,
                target_columns=list(fk.target_columns)
            )
            for fk in table_config.foreign_keys
        ]

        return cls(
            table_name=table_config.table_name,
            table_kind=table_config.table_kind.value,
            columns=columns,
            primary_key_fields=primary_key_fields,
            foreign_keys=foreign_keys,
            load_mode=table_config.load.mode.value,
            record_hash_enabled=table_config.load.record_hash,
        )
