from __future__ import annotations

from pathlib import Path

from semantic_finance_etl.config.loaders.project_loader import load_project_config
from semantic_finance_etl.config.models.project_config import ProjectConfig
from semantic_finance_etl.config.services.config_validation_service import (
    ConfigValidationService,
)


class ProjectConfigService:
    def __init__(self) -> None:
        self._validation_service = ConfigValidationService()

    def load(self, config_root: str | Path) -> ProjectConfig:
        project_config = load_project_config(config_root)
        self._validation_service.validate(project_config)
        return project_config

    