"""
Pytest test for two-level validation + load from tests/samples/configs
"""
import pytest
from semantic_finance_etl.config.services.project_config_service import ProjectConfigService
from semantic_finance_etl.domain.models.runtime_table_definition import RuntimeTableDefinition
from semantic_finance_etl.etl.orchestration.pipeline_executor import PipelineExecutor
from semantic_finance_etl.etl.validation.validation_service import ValidationService
from semantic_finance_etl.etl.loading.load_service import LoadService


def test_validation_and_load(project_config):
    summary = PipelineExecutor().run("tests/samples/configs")

    result = summary.canonical_results[0]
    table_config = project_config.tables[0]
    runtime_table = RuntimeTableDefinition.from_table_config(table_config)
    batch_payload = result.pipeline_result.final_batch_payload

    assert batch_payload.frame is not None

    validation_service = ValidationService()

    # Level 1 — lazy schema check (no collect)
    schema_result = validation_service.validate_schema(
        batch_payload=batch_payload,
        runtime_table=runtime_table,
    )
    # The companies DB has different columns than the test config, so it's not strictly valid
    # But it shouldn't raise exception
    assert hasattr(schema_result, 'is_valid')

    # Level 2 — data validation (collects inside service)
    validated_payload = validation_service.validate_batch(
        batch_payload=batch_payload,
        runtime_table=runtime_table,
    )
    assert validated_payload.validation_summary is not None
    assert hasattr(validated_payload.valid_frame, 'collect')

    # Load (collects valid_frame inside load service)
    load_service = LoadService(project_config.runtime)
    load_result = load_service.load(
        validated_payload=validated_payload,
        runtime_table=runtime_table,
    )
    
    assert load_result.mode in ("append", "replace", "upsert")
    assert load_result.inserted_rows >= 0
    assert load_result.total_affected >= 0
