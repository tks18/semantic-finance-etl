from semantic_finance_etl.config.services.project_config_service import (
    ProjectConfigService,
)

config = ProjectConfigService().load("tests/samples/configs")
print(config.model_dump())
