"""
Pytest test for simple parsing of a full YAML definition.
"""
import yaml
from semantic_finance_etl.config.models.project_config import ProjectConfig

def test_simple_parsing():
    with open("tests/samples/configs/full_definition.yaml", "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    project = ProjectConfig.model_validate(raw)
    assert project.project.project_id == "finance_etl"
    assert len(project.sources) > 0
    assert len(project.tables) > 0
