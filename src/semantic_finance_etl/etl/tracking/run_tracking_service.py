from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class RunRecord:
    """A persistent record of one ETL run lifecycle."""

    run_id: str
    project_id: str
    status: str       # "started" | "completed" | "failed"
    started_at: str   # ISO-8601 UTC
    completed_at: str | None = None
    duration_seconds: float | None = None
    source_count: int = 0
    table_count: int = 0
    total_rows_loaded: int = 0
    total_rows_invalid: int = 0
    error_message: str | None = None


@dataclass(slots=True)
class RunSummary:
    """Aggregate counts from a completed pipeline run."""

    source_count: int = 0
    table_count: int = 0
    total_rows_loaded: int = 0
    total_rows_invalid: int = 0
    table_results: list[dict[str, Any]] = field(default_factory=list)


RUN_TRACKING_TABLE = "etl_run_tracking"
RUN_TRACKING_DDL = f"""
CREATE TABLE IF NOT EXISTS {RUN_TRACKING_TABLE} (
    run_id              TEXT    PRIMARY KEY,
    project_id          TEXT    NOT NULL,
    status              TEXT    NOT NULL,
    started_at          TEXT    NOT NULL,
    completed_at        TEXT,
    duration_seconds    REAL,
    source_count        INTEGER DEFAULT 0,
    table_count         INTEGER DEFAULT 0,
    total_rows_loaded   INTEGER DEFAULT 0,
    total_rows_invalid  INTEGER DEFAULT 0,
    error_message       TEXT
)
"""


class RunTrackingService:
    """Records ETL run lifecycle events to a SQLite tracking table.

    Covers three states:
    - ``start_run``    — run begins; row inserted with status "started".
    - ``complete_run`` — run finishes; row updated with counts and duration.
    - ``fail_run``     — run errors; row updated with status "failed" and message.
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_tracking_table()

    def start_run(self, run_id: str, project_id: str) -> None:
        """Record that a new ETL run has started."""
        sql = f"""
        INSERT OR IGNORE INTO {RUN_TRACKING_TABLE}
            (run_id, project_id, status, started_at)
        VALUES (?, ?, 'started', ?)
        """
        connection = sqlite3.connect(str(self._db_path))
        try:
            connection.execute(sql, (run_id, project_id, _now_utc()))
            connection.commit()
        finally:
            connection.close()

    def complete_run(self, run_id: str, summary: RunSummary) -> None:
        """Record that a run completed successfully, with aggregate counts."""
        completed_at = _now_utc()
        started_at = self._get_started_at(run_id)
        duration = _duration_seconds(started_at, completed_at)

        sql = f"""
        UPDATE {RUN_TRACKING_TABLE}
        SET
            status              = 'completed',
            completed_at        = ?,
            duration_seconds    = ?,
            source_count        = ?,
            table_count         = ?,
            total_rows_loaded   = ?,
            total_rows_invalid  = ?
        WHERE run_id = ?
        """
        connection = sqlite3.connect(str(self._db_path))
        try:
            connection.execute(
                sql,
                (
                    completed_at,
                    duration,
                    summary.source_count,
                    summary.table_count,
                    summary.total_rows_loaded,
                    summary.total_rows_invalid,
                    run_id,
                ),
            )
            connection.commit()
        finally:
            connection.close()

    def fail_run(self, run_id: str, error: str) -> None:
        """Record that a run failed, capturing the error message."""
        completed_at = _now_utc()
        started_at = self._get_started_at(run_id)
        duration = _duration_seconds(started_at, completed_at)

        sql = f"""
        UPDATE {RUN_TRACKING_TABLE}
        SET
            status           = 'failed',
            completed_at     = ?,
            duration_seconds = ?,
            error_message    = ?
        WHERE run_id = ?
        """
        connection = sqlite3.connect(str(self._db_path))
        try:
            connection.execute(sql, (completed_at, duration, error, run_id))
            connection.commit()
        finally:
            connection.close()

    def get_run(self, run_id: str) -> RunRecord | None:
        """Retrieve the run record for a given run ID, or ``None``."""
        connection = sqlite3.connect(str(self._db_path))
        connection.row_factory = sqlite3.Row
        try:
            cursor = connection.cursor()
            cursor.execute(
                f"SELECT * FROM {RUN_TRACKING_TABLE} WHERE run_id = ?",
                (run_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            d = dict(row)
            return RunRecord(
                run_id=d["run_id"],
                project_id=d["project_id"],
                status=d["status"],
                started_at=d["started_at"],
                completed_at=d.get("completed_at"),
                duration_seconds=d.get("duration_seconds"),
                source_count=d.get("source_count", 0),
                table_count=d.get("table_count", 0),
                total_rows_loaded=d.get("total_rows_loaded", 0),
                total_rows_invalid=d.get("total_rows_invalid", 0),
                error_message=d.get("error_message"),
            )
        finally:
            connection.close()

    def list_runs(self, limit: int = 50) -> list[dict[str, Any]]:
        """List the most recent ETL runs, newest first."""
        if limit < 0:
            raise ValueError(f"Limit cannot be negative: {limit}")
        connection = sqlite3.connect(str(self._db_path))
        connection.row_factory = sqlite3.Row
        try:
            cursor = connection.cursor()
            cursor.execute(
                f"SELECT * FROM {RUN_TRACKING_TABLE} ORDER BY started_at DESC LIMIT ?",
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            connection.close()

    def _get_started_at(self, run_id: str) -> str | None:
        connection = sqlite3.connect(str(self._db_path))
        try:
            cursor = connection.cursor()
            cursor.execute(
                f"SELECT started_at FROM {RUN_TRACKING_TABLE} WHERE run_id = ?",
                (run_id,),
            )
            row = cursor.fetchone()
            return row[0] if row else None
        finally:
            connection.close()

    def _ensure_tracking_table(self) -> None:
        connection = sqlite3.connect(str(self._db_path))
        try:
            connection.execute(RUN_TRACKING_DDL)
            connection.commit()
        finally:
            connection.close()


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _duration_seconds(started_at: str | None, completed_at: str) -> float | None:
    if started_at is None:
        return None
    try:
        start = datetime.fromisoformat(started_at)
        end = datetime.fromisoformat(completed_at)
        return (end - start).total_seconds()
    except (ValueError, TypeError):
        return None
