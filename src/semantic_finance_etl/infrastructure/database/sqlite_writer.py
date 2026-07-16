from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import polars as pl

from semantic_finance_etl.domain.models.runtime_table_definition import (
    RuntimeColumnDefinition,
    RuntimeTableDefinition,
)


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

        for column in runtime_table.columns:
            sqlite_type = self._map_type_to_sqlite(column)
            nullable_sql = "" if column.nullable else " NOT NULL"
            column_sql.append(f"{column.name} {sqlite_type}{nullable_sql}")

        if runtime_table.primary_key_fields:
            primary_key_sql = (
                ", PRIMARY KEY (" + ", ".join(runtime_table.primary_key_fields) + ")"
            )

        foreign_key_sql_list = []
        for fk in getattr(runtime_table, "foreign_keys", []):
            fk_cols = ", ".join(fk.columns)
            target_cols = ", ".join(fk.target_columns)
            foreign_key_sql_list.append(
                f"FOREIGN KEY ({fk_cols}) REFERENCES {fk.target_table}({target_cols})"
            )
        
        fk_sql = (", " + ", ".join(foreign_key_sql_list)) if foreign_key_sql_list else ""

        create_sql = (
            f"CREATE TABLE IF NOT EXISTS {runtime_table.table_name} ("
            + ", ".join(column_sql)
            + primary_key_sql
            + fk_sql
            + ")"
        )
        connection.execute(create_sql)

        # Create indexes for indexed columns
        for column in runtime_table.columns:
            if column.indexed:
                idx_name = f"idx_{runtime_table.table_name}_{column.name}"
                connection.execute(
                    f"CREATE INDEX IF NOT EXISTS {idx_name} ON {runtime_table.table_name}({column.name})"
                )

    def _truncate_table(
        self,
        connection: sqlite3.Connection,
        table_name: str,
    ) -> None:
        connection.execute(f"DELETE FROM {table_name}")

    def _insert_dataframe(
        self,
        connection: sqlite3.Connection,
        runtime_table: RuntimeTableDefinition,
        df: pl.DataFrame,
    ) -> int:
        if len(df) == 0:
            return 0

        columns = runtime_table.column_names
        placeholders = ", ".join(["?"] * len(columns))
        column_sql = ", ".join(columns)

        sql = (
            f"INSERT INTO {runtime_table.table_name} ({column_sql}) "
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

        columns = runtime_table.column_names
        placeholders = ", ".join(["?"] * len(columns))
        column_sql = ", ".join(columns)

        update_columns = [
            col for col in columns if col not in runtime_table.primary_key_fields
        ]
        update_sql = ", ".join([f"{col}=excluded.{col}" for col in update_columns])

        sql = (
            f"INSERT INTO {runtime_table.table_name} ({column_sql}) "
            f"VALUES ({placeholders}) "
            f"ON CONFLICT ({', '.join(runtime_table.primary_key_fields)}) "
            f"DO UPDATE SET {update_sql}"
        )

        values = [
            [self._normalize_value(row.get(col)) for col in columns]
            for row in df.to_dicts()
        ]

        connection.executemany(sql, values)
        return (len(df), 0)

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
