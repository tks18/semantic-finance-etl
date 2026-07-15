from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from semantic_finance_etl.config.models.source_config import ReaderConfig, SourceConfig
from semantic_finance_etl.contracts.source_reader import SourceReader
from semantic_finance_etl.domain.models.hook_payloads import DiscoveredAsset, ReadPayload


class SQLiteQuerySourceReader(SourceReader[None]):
    reader_name = "sqlite_query"

    def read_asset(
        self,
        source_config: SourceConfig,
        reader_config: ReaderConfig,
        asset: DiscoveredAsset,
        params: None = None,
    ) -> ReadPayload:
        if reader_config.type != self.reader_name:
            raise ValueError(
                f"SQLiteQuerySourceReader cannot handle reader type "
                f"'{reader_config.type}'. Expected '{self.reader_name}'."
            )

        if not reader_config.sql or not reader_config.sql.strip():
            raise ValueError(
                f"Reader config for source '{source_config.source_id}' must define SQL."
            )

        db_path = Path(asset.path)
        if not db_path.exists():
            raise FileNotFoundError(f"SQLite source file not found: {db_path}")

        rows = self._execute_query(
            db_path=db_path,
            sql=reader_config.sql,
        )

        inferred_schema = self._infer_schema(rows)

        return ReadPayload(
            asset=asset,
            frame=rows,
            inferred_schema=inferred_schema,
            parse_metadata={
                "reader_type": self.reader_name,
                "sql": reader_config.sql,
                "row_count": len(rows),
                "db_path": str(db_path),
            },
            lineage_refs=[
                asset.path,
                source_config.source_id,
            ],
        )

    def _execute_query(
        self,
        *,
        db_path: Path,
        sql: str,
    ) -> list[dict[str, Any]]:
        connection = sqlite3.connect(str(db_path))
        connection.row_factory = sqlite3.Row

        try:
            cursor = connection.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()

            return [dict(row) for row in rows]
        finally:
            connection.close()

    def _infer_schema(
        self,
        rows: list[dict[str, Any]],
    ) -> dict[str, str]:
        if not rows:
            return {}

        first_row = rows[0]
        inferred: dict[str, str] = {}

        for column_name, value in first_row.items():
            inferred[column_name] = self._python_value_to_type_name(value)

        return inferred

    def _python_value_to_type_name(self, value: Any) -> str:
        if value is None:
            return "unknown"
        if isinstance(value, bool):
            return "bool"
        if isinstance(value, int):
            return "int"
        if isinstance(value, float):
            return "float"
        if isinstance(value, bytes):
            return "bytes"
        if isinstance(value, str):
            return "str"
        return type(value).__name__
