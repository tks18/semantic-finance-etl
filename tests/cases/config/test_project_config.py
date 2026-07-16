"""
pytest tests — config layer
Tests ProjectConfigService, ProjectConfig validation, and runtime config loading
using tests/samples/configs.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from semantic_finance_etl.config.models.project_config import ProjectConfig
from semantic_finance_etl.config.services.project_config_service import ProjectConfigService
from semantic_finance_etl.domain.enums.table_kind import TableKind

SAMPLE_CONFIGS = "tests/samples/configs"


class TestProjectConfigLoading:
    def test_loads_project_metadata(self, project_config: ProjectConfig):
        assert project_config.project.project_id == "finance_etl"
        assert project_config.project.name == "Finance ETL"

    def test_has_at_least_one_source(self, project_config: ProjectConfig):
        assert len(project_config.sources) >= 1

    def test_source_id_is_investment_backups(self, project_config: ProjectConfig):
        source_ids = [s.source_id for s in project_config.sources]
        assert "investment_backups" in source_ids

    def test_has_at_least_one_table(self, project_config: ProjectConfig):
        assert len(project_config.tables) >= 1

    def test_table_name_is_companies(self, project_config: ProjectConfig):
        table_names = [t.table_name for t in project_config.tables]
        assert "companies" in table_names

    def test_table_kind_is_canonical(self, project_config: ProjectConfig):
        table = next(t for t in project_config.tables if t.table_name == "companies")
        assert table.table_kind == TableKind.CANONICAL

    def test_table_has_columns_defined(self, project_config: ProjectConfig):
        table = next(t for t in project_config.tables if t.table_name == "companies")
        assert len(table.columns) >= 1

    def test_runtime_has_db_path(self, project_config: ProjectConfig):
        assert project_config.runtime.local_db_path is not None
        assert "app4.db" in project_config.runtime.local_db_path

    def test_runtime_has_hook_search_paths(self, project_config: ProjectConfig):
        assert len(project_config.runtime.hook_search_paths) >= 1

    def test_source_reader_type_is_sqlite_query(self, project_config: ProjectConfig):
        source = project_config.sources[0]
        assert source.reader.type == "sqlite_query"
        assert source.reader.sql is not None

    def test_source_target_tables_references_existing_table(self, project_config: ProjectConfig):
        table_names = {t.table_name for t in project_config.tables}
        for source in project_config.sources:
            for target in source.target_tables:
                assert target in table_names, (
                    f"Source '{source.source_id}' references unknown table '{target}'"
                )

    def test_config_service_raises_on_bad_path(self):
        with pytest.raises(Exception):
            ProjectConfigService().load("non/existent/path")
