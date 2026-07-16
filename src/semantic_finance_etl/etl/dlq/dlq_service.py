from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import polars as pl


@dataclass(slots=True)
class DLQRow:
    """A single row persisted in the Dead-Letter Queue table."""

    run_id: str
    stage: str
    source_id: str
    table_name: str
    raw_row_json: str
    error_message: str
    persisted_at: str  # ISO-8601 UTC string


@dataclass(slots=True)
class DLQSummary:
    """Summary of a DLQ persist operation."""

    table_name: str
    run_id: str
    stage: str
    persisted_row_count: int
    skipped: bool = False
    skip_reason: str | None = None


DLQ_TABLE_NAME = "etl_dlq"
DLQ_DDL = f"""
CREATE TABLE IF NOT EXISTS {DLQ_TABLE_NAME} (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      TEXT    NOT NULL,
    stage       TEXT    NOT NULL,
    source_id   TEXT    NOT NULL,
    table_name  TEXT    NOT NULL,
    raw_row_json TEXT   NOT NULL,
    error_message TEXT  NOT NULL,
    persisted_at TEXT   NOT NULL
)
"""


class DLQService:
    """Persists invalid rows into the Dead-Letter Queue (DLQ) SQLite table.

    The DLQ captures rows that failed validation so they can be reviewed,
    corrected, and re-submitted without data loss.

    Collect boundary:
        This service calls ``.collect()`` on the ``invalid_frame`` — it is the
        designated boundary for invalid row materialization.
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_dlq_table()

    def persist_invalid_rows(
        self,
        invalid_frame: pl.LazyFrame | None,
        *,
        stage: str,
        source_id: str,
        table_name: str,
        run_id: str,
        error_message: str = "Row failed validation.",
    ) -> DLQSummary:
        """Persist all invalid rows from a lazy frame to the DLQ table.

        Parameters
        ----------
        invalid_frame:
            The ``invalid_frame`` from a ``ValidatedBatchPayload``.
            If ``None`` or empty, the operation is a no-op.
        stage, source_id, table_name, run_id:
            Metadata attached to every DLQ row.
        error_message:
            Default error description when a row does not carry its own.
        """
        if invalid_frame is None:
            return DLQSummary(
                table_name=table_name,
                run_id=run_id,
                stage=stage,
                persisted_row_count=0,
                skipped=True,
                skip_reason="invalid_frame was None.",
            )

        # --- Explicit collect boundary for invalid rows ---
        df: pl.DataFrame = invalid_frame.collect()

        if len(df) == 0:
            return DLQSummary(
                table_name=table_name,
                run_id=run_id,
                stage=stage,
                persisted_row_count=0,
                skipped=True,
                skip_reason="invalid_frame was empty after collect.",
            )

        now_utc = datetime.now(timezone.utc).isoformat()
        dlq_rows: list[DLQRow] = []

        for row_dict in df.to_dicts():
            # If the validation service attached __error_messages__, use it.
            row_error = str(row_dict.pop("__error_messages__", error_message) or error_message)
            row_dict.pop("__has_error__", None)

            dlq_rows.append(
                DLQRow(
                    run_id=run_id,
                    stage=stage,
                    source_id=source_id,
                    table_name=table_name,
                    raw_row_json=json.dumps(row_dict, default=str),
                    error_message=row_error,
                    persisted_at=now_utc,
                )
            )

        persisted = self._insert_dlq_rows(dlq_rows)

        return DLQSummary(
            table_name=table_name,
            run_id=run_id,
            stage=stage,
            persisted_row_count=persisted,
        )

    def get_dlq_rows_for_run(self, run_id: str) -> list[dict[str, Any]]:
        """Retrieve all DLQ rows for a given run ID."""
        connection = sqlite3.connect(str(self._db_path))
        connection.row_factory = sqlite3.Row
        try:
            cursor = connection.cursor()
            cursor.execute(
                f"SELECT * FROM {DLQ_TABLE_NAME} WHERE run_id = ?", (run_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            connection.close()

    def get_dlq_rows_for_table(self, table_name: str) -> list[dict[str, Any]]:
        """Retrieve all DLQ rows for a given target table name."""
        connection = sqlite3.connect(str(self._db_path))
        connection.row_factory = sqlite3.Row
        try:
            cursor = connection.cursor()
            cursor.execute(
                f"SELECT * FROM {DLQ_TABLE_NAME} WHERE table_name = ?", (table_name,)
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            connection.close()

    def _ensure_dlq_table(self) -> None:
        connection = sqlite3.connect(str(self._db_path))
        try:
            connection.execute(DLQ_DDL)
            connection.commit()
        finally:
            connection.close()

    def _insert_dlq_rows(self, rows: list[DLQRow]) -> int:
        if not rows:
            return 0

        sql = f"""
        INSERT INTO {DLQ_TABLE_NAME}
            (run_id, stage, source_id, table_name, raw_row_json, error_message, persisted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        connection = sqlite3.connect(str(self._db_path))
        try:
            connection.executemany(
                sql,
                [
                    (
                        r.run_id,
                        r.stage,
                        r.source_id,
                        r.table_name,
                        r.raw_row_json,
                        r.error_message,
                        r.persisted_at,
                    )
                    for r in rows
                ],
            )
            connection.commit()
            return len(rows)
        finally:
            connection.close()
