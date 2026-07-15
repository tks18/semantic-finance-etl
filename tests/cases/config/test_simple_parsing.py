import yaml
from semantic_finance_etl.config.models.project_config import ProjectConfig

with open("tests/samples/configs/full_definition.yaml", "r", encoding="utf-8") as f:
    raw = yaml.safe_load(f)

project = ProjectConfig.model_validate(raw)
print(project.model_dump())
