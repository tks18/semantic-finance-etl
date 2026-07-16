from __future__ import annotations

import sqlite3
from pathlib import Path

import polars as pl

from semantic_finance_etl.config.models.source_config import ReaderConfig, SourceConfig
from semantic_finance_etl.contracts.source_reader import SourceReader
from semantic_finance_etl.domain.models.data_schema import DataSchema
from semantic_finance_etl.domain.models.hook_payloads import DiscoveredAsset, ReadPayload


class SQLiteQuerySourceReader(SourceReader[None]):
    """Reads data from a SQLite database using a configured SQL query.

    Returns a ``ReadPayload`` whose ``frame`` is a ``pl.LazyFrame``.
    The query result is loaded into a Polars ``DataFrame`` and immediately
    converted to ``.lazy()`` so no materialization escapes this boundary.
    Schema is inferred from the Polars dtype map and attached as a ``DataSchema``.
    """

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

        df = self._execute_query(db_path=db_path, sql=reader_config.sql)
        lazy_frame = df.lazy()
        inferred_schema = DataSchema.infer_from_polars_schema(df.schema)

        return ReadPayload(
            asset=asset,
            frame=lazy_frame,
            data_schema=inferred_schema,
            parse_metadata={
                "reader_type": self.reader_name,
                "sql": reader_config.sql,
                "row_count": len(df),
                "db_path": str(db_path),
            },
            lineage_refs=[
                asset.path,
                source_config.source_id,
            ],
        )

    def _execute_query(self, *, db_path: Path, sql: str) -> pl.DataFrame:
        """Execute SQL and return a Polars DataFrame.

        This is the single materialization point for the reader.
        The result is immediately converted to ``.lazy()`` by the caller.
        """
        connection = sqlite3.connect(str(db_path))

        try:
            return pl.read_database(query=sql, connection=connection)
        finally:
            connection.close()
