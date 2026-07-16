from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import polars as pl

from semantic_finance_etl.domain.models.runtime_table_definition import (
    RuntimeColumnDefinition,
    RuntimeTableDefinition,
)
import re

def _val_id(name: str) -> str:
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name):
        raise ValueError(f"Invalid SQLite identifier: {name}")
    return name


class SQLiteWriter:
    """Writes Polars DataFrames to SQLite.

    All writes accept a materialized ``pl.DataFrame`` produced by the load
    service at the explicit collection boundary.  No ``list[dict]`` API exists.
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

    def write_dataframe(
        self,
        runtime_table: RuntimeTableDefinition,
        df: pl.DataFrame,
        mode: str | None = None,
    ) -> dict[str, Any]:
        """Write a materialized ``pl.DataFrame`` to the target SQLite table.

        Parameters
        ----------
        runtime_table:
            Runtime table definition supplying DDL metadata.
        df:
            Already-collected ``pl.DataFrame`` — ``LazyFrame.collect()``
            must have been called upstream (by ``LoadService``).
        mode:
            Load mode: ``"append"``, ``"replace"``, or ``"upsert"``.
            Falls back to ``runtime_table.load_mode`` when ``None``.
        """
        effective_mode = mode or runtime_table.load_mode

        connection = sqlite3.connect(str(self._db_path))
        try:
            self._ensure_table(connection, runtime_table)

            if effective_mode == "replace":
                self._truncate_table(connection, runtime_table.table_name)
                inserted = self._insert_dataframe(connection, runtime_table, df)
                connection.commit()
                return {"mode": effective_mode, "inserted_rows": inserted, "updated_rows": 0}

            if effective_mode == "append":
                inserted = self._insert_dataframe(connection, runtime_table, df)
                connection.commit()
                return {"mode": effective_mode, "inserted_rows": inserted, "updated_rows": 0}

            if effective_mode == "upsert":
                inserted, updated = self._upsert_dataframe(connection, runtime_table, df)
                connection.commit()
                return {"mode": effective_mode, "inserted_rows": inserted, "updated_rows": updated}

            raise ValueError(f"Unsupported SQLite write mode: {effective_mode}")
        finally:
            connection.close()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _ensure_table(
        self,
        connection: sqlite3.Connection,
        runtime_table: RuntimeTableDefinition,
    ) -> None:
        column_sql: list[str] = []
        primary_key_sql = ""

        table_name = _val_id(runtime_table.table_name)
        for column in runtime_table.columns:
            col_name = _val_id(column.name)
            sqlite_type = self._map_type_to_sqlite(column)
            nullable_sql = "" if column.nullable else " NOT NULL"
            column_sql.append(f"{col_name} {sqlite_type}{nullable_sql}")

        if runtime_table.primary_key_fields:
            pk_fields = [_val_id(pk) for pk in runtime_table.primary_key_fields]
            primary_key_sql = (
                ", PRIMARY KEY (" + ", ".join(pk_fields) + ")"
            )

        foreign_key_sql_list = []
        for fk in getattr(runtime_table, "foreign_keys", []):
            fk_cols = ", ".join([_val_id(c) for c in fk.columns])
            target_table = _val_id(fk.target_table)
            target_cols = ", ".join([_val_id(c) for c in fk.target_columns])
            foreign_key_sql_list.append(
                f"FOREIGN KEY ({fk_cols}) REFERENCES {target_table}({target_cols})"
            )
        
        fk_sql = (", " + ", ".join(foreign_key_sql_list)) if foreign_key_sql_list else ""

        create_sql = (
            f"CREATE TABLE IF NOT EXISTS {table_name} ("
            + ", ".join(column_sql)
            + primary_key_sql
            + fk_sql
            + ")"
        )
        connection.execute(create_sql)

        # Create indexes for indexed columns
        for column in runtime_table.columns:
            if column.indexed:
                col_name = _val_id(column.name)
                idx_name = _val_id(f"idx_{table_name}_{col_name}")
                connection.execute(
                    f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name}({col_name})"
                )

    def _truncate_table(
        self,
        connection: sqlite3.Connection,
        table_name: str,
    ) -> None:
        table_name = _val_id(table_name)
        connection.execute(f"DELETE FROM {table_name}")

    def _insert_dataframe(
        self,
        connection: sqlite3.Connection,
        runtime_table: RuntimeTableDefinition,
        df: pl.DataFrame,
    ) -> int:
        if len(df) == 0:
            return 0

        columns = [_val_id(c) for c in runtime_table.column_names]
        table_name = _val_id(runtime_table.table_name)
        placeholders = ", ".join(["?"] * len(columns))
        column_sql = ", ".join(columns)

        sql = (
            f"INSERT INTO {table_name} ({column_sql}) "
            f"VALUES ({placeholders})"
        )

        values = [
            [self._normalize_value(row.get(col)) for col in columns]
            for row in df.to_dicts()
        ]

        connection.executemany(sql, values)
        return len(df)

    def _upsert_dataframe(
        self,
        connection: sqlite3.Connection,
        runtime_table: RuntimeTableDefinition,
        df: pl.DataFrame,
    ) -> tuple[int, int]:
        if len(df) == 0:
            return (0, 0)

        if not runtime_table.primary_key_fields:
            inserted = self._insert_dataframe(connection, runtime_table, df)
            return (inserted, 0)

        table_name = _val_id(runtime_table.table_name)
        columns = [_val_id(c) for c in runtime_table.column_names]
        pk_cols = [_val_id(c) for c in runtime_table.primary_key_fields]
        
        placeholders = ", ".join(["?"] * len(columns))
        column_sql = ", ".join(columns)

        update_columns = [
            col for col in columns if col not in pk_cols
        ]
        update_sql = ", ".join([f"{col}=excluded.{col}" for col in update_columns])

        sql = (
            f"INSERT INTO {table_name} ({column_sql}) "
            f"VALUES ({placeholders}) "
            f"ON CONFLICT ({', '.join(pk_cols)}) "
            f"DO UPDATE SET {update_sql}"
        )

        values = [
            [self._normalize_value(row.get(col)) for col in runtime_table.column_names]
            for row in df.to_dicts()
        ]
        
        # Accurately count updated vs inserted rows
        cursor = connection.cursor()
        pk_values = [tuple(row.get(col) for col in runtime_table.primary_key_fields) for row in df.to_dicts()]
        existing_count = 0
        batch_size = 500
        for i in range(0, len(pk_values), batch_size):
            batch = pk_values[i:i+batch_size]
            in_placeholders = ",".join(["(" + ",".join(["?"] * len(pk_cols)) + ")"] * len(batch))
            flat_batch = [item for sublist in batch for item in sublist]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE ({', '.join(pk_cols)}) IN ({in_placeholders})", flat_batch)
            existing_count += cursor.fetchone()[0]
            
        updated = existing_count
        inserted = len(df) - existing_count

        connection.executemany(sql, values)
        return (inserted, updated)

    def _map_type_to_sqlite(self, column: RuntimeColumnDefinition) -> str:
        type_name = column.type_name.strip().lower()

        if type_name in {"str", "string", "text", "date", "datetime", "timestamp"}:
            return "TEXT"
        if type_name in {"int", "integer", "bool", "boolean"}:
            return "INTEGER"
        if type_name in {"float", "double", "real", "decimal", "numeric", "number"}:
            return "REAL"
        if type_name in {"bytes", "blob"}:
            return "BLOB"

        return "TEXT"

    def _normalize_value(self, value: Any) -> Any:
        if isinstance(value, bool):
            return int(value)
        return value
