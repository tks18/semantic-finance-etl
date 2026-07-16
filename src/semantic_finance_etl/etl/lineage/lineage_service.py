from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class LineageEvent:
    """A single recorded lineage event in the ETL run."""

    event_id: int | None
    run_id: str
    event_type: str   # "file" | "hook" | "stage" | "output"
    source_ref: str
    target_ref: str
    stage: str | None
    hook_name: str | None
    table_name: str | None
    recorded_at: str  # ISO-8601 UTC


LINEAGE_TABLE_NAME = "etl_lineage"
LINEAGE_DDL = f"""
CREATE TABLE IF NOT EXISTS {LINEAGE_TABLE_NAME} (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      TEXT    NOT NULL,
    event_type  TEXT    NOT NULL,
    source_ref  TEXT    NOT NULL,
    target_ref  TEXT    NOT NULL,
    stage       TEXT,
    hook_name   TEXT,
    table_name  TEXT,
    recorded_at TEXT    NOT NULL
)
"""


class LineageService:
    """Records ETL lineage events to a SQLite table.

    Lineage types:
    - ``file``   — a source file was read into a table.
    - ``hook``   — a hook transformed data in a stage.
    - ``stage``  — a stage completed (covers multiple hooks).
    - ``output`` — an output (table or semantic doc) was produced.

    All event types share the same ``etl_lineage`` table, differentiated
    by the ``event_type`` column.
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_lineage_table()

    def record_file_lineage(
        self,
        *,
        run_id: str,
        source_path: str,
        table_name: str,
        stage: str = "read",
    ) -> None:
        """Record that a source file contributed rows to a target table."""
        self._insert_event(
            LineageEvent(
                event_id=None,
                run_id=run_id,
                event_type="file",
                source_ref=source_path,
                target_ref=table_name,
                stage=stage,
                hook_name=None,
                table_name=table_name,
                recorded_at=_now_utc(),
            )
        )

    def record_hook_lineage(
        self,
        *,
        run_id: str,
        hook_name: str,
        stage: str,
        table_name: str,
        source_ref: str = "",
    ) -> None:
        """Record that a hook ran against a table in a given stage."""
        self._insert_event(
            LineageEvent(
                event_id=None,
                run_id=run_id,
                event_type="hook",
                source_ref=source_ref or table_name,
                target_ref=table_name,
                stage=stage,
                hook_name=hook_name,
                table_name=table_name,
                recorded_at=_now_utc(),
            )
        )

    def record_stage_lineage(
        self,
        *,
        run_id: str,
        stage: str,
        table_name: str,
        source_ref: str = "",
    ) -> None:
        """Record that a full stage completed for a table."""
        self._insert_event(
            LineageEvent(
                event_id=None,
                run_id=run_id,
                event_type="stage",
                source_ref=source_ref or table_name,
                target_ref=table_name,
                stage=stage,
                hook_name=None,
                table_name=table_name,
                recorded_at=_now_utc(),
            )
        )

    def record_output_lineage(
        self,
        *,
        run_id: str,
        table_name: str,
        output_ref: str,
        stage: str = "load",
    ) -> None:
        """Record that a table was successfully written to storage."""
        self._insert_event(
            LineageEvent(
                event_id=None,
                run_id=run_id,
                event_type="output",
                source_ref=table_name,
                target_ref=output_ref,
                stage=stage,
                hook_name=None,
                table_name=table_name,
                recorded_at=_now_utc(),
            )
        )

    def get_lineage_for_run(self, run_id: str) -> list[dict[str, Any]]:
        """Retrieve all lineage events for a given run ID."""
        connection = sqlite3.connect(str(self._db_path))
        connection.row_factory = sqlite3.Row
        try:
            cursor = connection.cursor()
            cursor.execute(
                f"SELECT * FROM {LINEAGE_TABLE_NAME} WHERE run_id = ? ORDER BY id",
                (run_id,),
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            connection.close()

    def get_lineage_for_table(self, table_name: str) -> list[dict[str, Any]]:
        """Retrieve all lineage events for a given target table."""
        connection = sqlite3.connect(str(self._db_path))
        connection.row_factory = sqlite3.Row
        try:
            cursor = connection.cursor()
            cursor.execute(
                f"SELECT * FROM {LINEAGE_TABLE_NAME} WHERE table_name = ? ORDER BY id",
                (table_name,),
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            connection.close()

    def _ensure_lineage_table(self) -> None:
        connection = sqlite3.connect(str(self._db_path))
        try:
            connection.execute(LINEAGE_DDL)
            connection.commit()
        finally:
            connection.close()

    def _insert_event(self, event: LineageEvent) -> None:
        sql = f"""
        INSERT INTO {LINEAGE_TABLE_NAME}
            (run_id, event_type, source_ref, target_ref, stage, hook_name, table_name, recorded_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        connection = sqlite3.connect(str(self._db_path))
        try:
            connection.execute(
                sql,
                (
                    event.run_id,
                    event.event_type,
                    event.source_ref,
                    event.target_ref,
                    event.stage,
                    event.hook_name,
                    event.table_name,
                    event.recorded_at,
                ),
            )
            connection.commit()
        finally:
            connection.close()


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()
