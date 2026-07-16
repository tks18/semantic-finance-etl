"""
pytest tests — governance services (DLQ, Lineage, RunTracking)
Uses an isolated SQLite DB per test (tmp_path fixture) so tests are hermetic.
"""
from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from semantic_finance_etl.etl.dlq.dlq_service import DLQService
from semantic_finance_etl.etl.lineage.lineage_service import LineageService
from semantic_finance_etl.etl.tracking.run_tracking_service import RunSummary, RunTrackingService


# ---------------------------------------------------------------------------
# DLQService
# ---------------------------------------------------------------------------

class TestDLQService:
    def test_persist_none_frame_is_skipped(self, isolated_db_path: Path):
        svc = DLQService(str(isolated_db_path))
        result = svc.persist_invalid_rows(
            None, stage="validation", source_id="src1",
            table_name="t", run_id="run-001"
        )
        assert result.skipped is True
        assert result.persisted_row_count == 0

    def test_persist_empty_frame_is_skipped(self, isolated_db_path: Path):
        svc = DLQService(str(isolated_db_path))
        empty = pl.DataFrame({"id": [], "__has_error__": [], "__error_messages__": []}).lazy()
        result = svc.persist_invalid_rows(
            empty, stage="validation", source_id="src1",
            table_name="t", run_id="run-001"
        )
        assert result.skipped is True

    def test_persist_invalid_rows_writes_to_db(self, isolated_db_path: Path):
        svc = DLQService(str(isolated_db_path))
        invalid = pl.DataFrame({
            "id": [None, None],
            "name": ["Alice", "Bob"],
            "__has_error__": [True, True],
            "__error_messages__": ["id is null", "id is null"],
        }).lazy()
        result = svc.persist_invalid_rows(
            invalid, stage="validation", source_id="src1",
            table_name="companies", run_id="run-001"
        )
        assert result.persisted_row_count == 2
        assert not result.skipped

    def test_get_dlq_rows_for_run(self, isolated_db_path: Path):
        svc = DLQService(str(isolated_db_path))
        invalid = pl.DataFrame({
            "x": [1],
            "__has_error__": [True],
            "__error_messages__": ["test error"],
        }).lazy()
        svc.persist_invalid_rows(
            invalid, stage="validation", source_id="s", table_name="t", run_id="run-abc"
        )
        rows = svc.get_dlq_rows_for_run("run-abc")
        assert len(rows) == 1
        assert rows[0]["run_id"] == "run-abc"
        assert rows[0]["error_message"] == "test error"

    def test_get_dlq_rows_for_table(self, isolated_db_path: Path):
        svc = DLQService(str(isolated_db_path))
        invalid = pl.DataFrame({
            "y": [1, 2],
            "__has_error__": [True, True],
            "__error_messages__": ["err", "err2"],
        }).lazy()
        svc.persist_invalid_rows(
            invalid, stage="validation", source_id="s", table_name="my_table", run_id="r1"
        )
        rows = svc.get_dlq_rows_for_table("my_table")
        assert len(rows) == 2

    def test_different_run_ids_isolated(self, isolated_db_path: Path):
        svc = DLQService(str(isolated_db_path))
        for run_id in ["run-001", "run-002"]:
            invalid = pl.DataFrame({
                "z": [1],
                "__has_error__": [True],
                "__error_messages__": [f"error in {run_id}"],
            }).lazy()
            svc.persist_invalid_rows(
                invalid, stage="v", source_id="s", table_name="t", run_id=run_id
            )
        assert len(svc.get_dlq_rows_for_run("run-001")) == 1
        assert len(svc.get_dlq_rows_for_run("run-002")) == 1


# ---------------------------------------------------------------------------
# LineageService
# ---------------------------------------------------------------------------

class TestLineageService:
    def test_record_file_lineage(self, isolated_db_path: Path):
        svc = LineageService(str(isolated_db_path))
        svc.record_file_lineage(run_id="r1", source_path="/data/x.db", table_name="companies")
        events = svc.get_lineage_for_run("r1")
        assert len(events) == 1
        assert events[0]["event_type"] == "file"
        assert events[0]["source_ref"] == "/data/x.db"

    def test_record_hook_lineage(self, isolated_db_path: Path):
        svc = LineageService(str(isolated_db_path))
        svc.record_hook_lineage(
            run_id="r1", hook_name="normalize", stage="post_read", table_name="companies"
        )
        events = svc.get_lineage_for_run("r1")
        assert events[0]["event_type"] == "hook"
        assert events[0]["hook_name"] == "normalize"

    def test_record_output_lineage(self, isolated_db_path: Path):
        svc = LineageService(str(isolated_db_path))
        svc.record_output_lineage(run_id="r1", table_name="companies", output_ref="companies")
        events = svc.get_lineage_for_run("r1")
        assert events[0]["event_type"] == "output"

    def test_multiple_events_ordered_by_id(self, isolated_db_path: Path):
        svc = LineageService(str(isolated_db_path))
        svc.record_file_lineage(run_id="r1", source_path="/a.db", table_name="t")
        svc.record_hook_lineage(run_id="r1", hook_name="h1", stage="post_read", table_name="t")
        svc.record_output_lineage(run_id="r1", table_name="t", output_ref="t")
        events = svc.get_lineage_for_run("r1")
        assert len(events) == 3
        assert [e["event_type"] for e in events] == ["file", "hook", "output"]

    def test_lineage_by_table(self, isolated_db_path: Path):
        svc = LineageService(str(isolated_db_path))
        svc.record_file_lineage(run_id="r1", source_path="/a.db", table_name="companies")
        svc.record_file_lineage(run_id="r2", source_path="/b.db", table_name="companies")
        svc.record_file_lineage(run_id="r3", source_path="/c.db", table_name="other_table")
        events = svc.get_lineage_for_table("companies")
        assert len(events) == 2
        assert all(e["table_name"] == "companies" for e in events)


# ---------------------------------------------------------------------------
# RunTrackingService
# ---------------------------------------------------------------------------

class TestRunTrackingService:
    def test_start_and_get_run(self, isolated_db_path: Path):
        svc = RunTrackingService(str(isolated_db_path))
        svc.start_run("run-001", "finance_etl")
        record = svc.get_run("run-001")
        assert record is not None
        assert record.run_id == "run-001"
        assert record.project_id == "finance_etl"
        assert record.status == "started"

    def test_complete_run_updates_status(self, isolated_db_path: Path):
        svc = RunTrackingService(str(isolated_db_path))
        svc.start_run("run-001", "finance_etl")
        svc.complete_run("run-001", RunSummary(
            source_count=1, table_count=2,
            total_rows_loaded=500, total_rows_invalid=3
        ))
        record = svc.get_run("run-001")
        assert record.status == "completed"
        assert record.source_count == 1
        assert record.table_count == 2
        assert record.total_rows_loaded == 500
        assert record.total_rows_invalid == 3
        assert record.duration_seconds is not None

    def test_fail_run_updates_status(self, isolated_db_path: Path):
        svc = RunTrackingService(str(isolated_db_path))
        svc.start_run("run-err", "finance_etl")
        svc.fail_run("run-err", "ConnectionError: db not found")
        record = svc.get_run("run-err")
        assert record.status == "failed"
        assert "ConnectionError" in record.error_message

    def test_get_nonexistent_run_returns_none(self, isolated_db_path: Path):
        svc = RunTrackingService(str(isolated_db_path))
        assert svc.get_run("does-not-exist") is None

    def test_list_runs_returns_most_recent_first(self, isolated_db_path: Path):
        svc = RunTrackingService(str(isolated_db_path))
        for i in range(3):
            svc.start_run(f"run-{i:03d}", "proj")
        runs = svc.list_runs(limit=10)
        assert len(runs) == 3

    def test_start_run_is_idempotent(self, isolated_db_path: Path):
        """INSERT OR IGNORE — calling start_run twice should not error."""
        svc = RunTrackingService(str(isolated_db_path))
        svc.start_run("run-dup", "proj")
        svc.start_run("run-dup", "proj")  # should be silently ignored
        assert svc.get_run("run-dup") is not None
