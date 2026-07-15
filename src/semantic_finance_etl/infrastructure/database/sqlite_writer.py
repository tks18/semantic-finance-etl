from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from semantic_finance_etl.domain.models.runtime_table_definition import (
    RuntimeColumnDefinition,
    RuntimeTableDefinition,
)


class SQLiteWriter:
    def __init__(self, db_path: str) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

    def write_rows(
        self,
        runtime_table: RuntimeTableDefinition,
        rows: list[dict[str, Any]],
        mode: str | None = None,
    ) -> dict[str, Any]:
        effective_mode = mode or runtime_table.load_mode

        connection = sqlite3.connect(str(self._db_path))

        try:
            self._ensure_table(connection, runtime_table)

            if effective_mode == "replace":
                self._truncate_table(connection, runtime_table.table_name)
                inserted = self._insert_rows(connection, runtime_table, rows)
                connection.commit()
                return {
                    "mode": effective_mode,
                    "inserted_rows": inserted,
                    "updated_rows": 0,
                }

            if effective_mode == "append":
                inserted = self._insert_rows(connection, runtime_table, rows)
                connection.commit()
                return {
                    "mode": effective_mode,
                    "inserted_rows": inserted,
                    "updated_rows": 0,
                }

            if effective_mode == "upsert":
                inserted, updated = self._upsert_rows(connection, runtime_table, rows)
                connection.commit()
                return {
                    "mode": effective_mode,
                    "inserted_rows": inserted,
                    "updated_rows": updated,
                }

            raise ValueError(f"Unsupported SQLite write mode: {effective_mode}")
        finally:
            connection.close()

    def _ensure_table(
        self,
        connection: sqlite3.Connection,
        runtime_table: RuntimeTableDefinition,
    ) -> None:
        column_sql = []
        primary_key_sql = ""

        for column in runtime_table.columns:
            sqlite_type = self._map_type_to_sqlite(column)
            nullable_sql = "" if column.nullable else " NOT NULL"
            column_sql.append(f"{column.name} {sqlite_type}{nullable_sql}")

        if runtime_table.primary_key_fields:
            primary_key_sql = (
                ", PRIMARY KEY (" + ", ".join(runtime_table.primary_key_fields) + ")"
            )

        create_sql = (
            f"CREATE TABLE IF NOT EXISTS {runtime_table.table_name} ("
            + ", ".join(column_sql)
            + primary_key_sql
            + ")"
        )

        connection.execute(create_sql)

    def _truncate_table(
        self,
        connection: sqlite3.Connection,
        table_name: str,
    ) -> None:
        connection.execute(f"DELETE FROM {table_name}")

    def _insert_rows(
        self,
        connection: sqlite3.Connection,
        runtime_table: RuntimeTableDefinition,
        rows: list[dict[str, Any]],
    ) -> int:
        if not rows:
            return 0

        columns = runtime_table.column_names
        placeholders = ", ".join(["?"] * len(columns))
        column_sql = ", ".join(columns)

        sql = (
            f"INSERT INTO {runtime_table.table_name} ({column_sql}) "
            f"VALUES ({placeholders})"
        )

        values = [
            [self._normalize_value(row.get(column)) for column in columns]
            for row in rows
        ]

        connection.executemany(sql, values)
        return len(rows)

    def _upsert_rows(
        self,
        connection: sqlite3.Connection,
        runtime_table: RuntimeTableDefinition,
        rows: list[dict[str, Any]],
    ) -> tuple[int, int]:
        if not rows:
            return (0, 0)

        if not runtime_table.primary_key_fields:
            inserted = self._insert_rows(connection, runtime_table, rows)
            return (inserted, 0)

        columns = runtime_table.column_names
        placeholders = ", ".join(["?"] * len(columns))
        column_sql = ", ".join(columns)

        update_columns = [
            column for column in columns if column not in runtime_table.primary_key_fields
        ]

        update_sql = ", ".join(
            [f"{column}=excluded.{column}" for column in update_columns]
        )

        sql = (
            f"INSERT INTO {runtime_table.table_name} ({column_sql}) "
            f"VALUES ({placeholders}) "
            f"ON CONFLICT ({', '.join(runtime_table.primary_key_fields)}) "
            f"DO UPDATE SET {update_sql}"
        )

        values = [
            [self._normalize_value(row.get(column)) for column in columns]
            for row in rows
        ]

        connection.executemany(sql, values)

        # sqlite executemany doesn't easily tell inserted vs updated row counts.
        # For now treat all as affected rows.
        return (len(rows), 0)

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
