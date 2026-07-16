"""
Shared pytest fixtures for all test cases.
All tests that need the sample project config or sample DB reference
tests/samples/configs and tests/samples/dbs/ via these fixtures.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from semantic_finance_etl.config.services.project_config_service import ProjectConfigService
from semantic_finance_etl.config.models.project_config import ProjectConfig

SAMPLE_CONFIGS = Path("tests/samples/configs")
SAMPLE_DB = Path("tests/samples/dbs/companies.db")
OUTPUT_DIR = Path("tests/output")


@pytest.fixture(scope="session")
def sample_configs_path() -> Path:
    """Absolute path to tests/samples/configs."""
    return SAMPLE_CONFIGS


@pytest.fixture(scope="session")
def sample_db_path() -> Path:
    """Absolute path to the sample companies.db SQLite file."""
    return SAMPLE_DB


@pytest.fixture(scope="session")
def project_config(sample_configs_path: Path) -> ProjectConfig:
    """Loaded project config from tests/samples/configs."""
    return ProjectConfigService().load(str(sample_configs_path))


@pytest.fixture()
def isolated_db_path(tmp_path: Path) -> Path:
    """A fresh SQLite DB path in a pytest tmp_path (auto-cleaned after each test)."""
    return tmp_path / "test.db"


@pytest.fixture(autouse=True)
def ensure_output_dir():
    """Ensure tests/output exists before each test."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

@pytest.fixture(autouse=True)
def cleanup_loggers():
    """Close and remove any log handlers to prevent Windows file locks during teardown."""
    yield
    import logging
    root_logger = logging.getLogger("semantic_finance_etl")
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)
