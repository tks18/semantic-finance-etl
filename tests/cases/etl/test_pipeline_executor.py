"""
Pytest test for full pipeline executor run.
"""
from semantic_finance_etl.etl.orchestration.pipeline_executor import PipelineExecutor
import pytest

def test_pipeline_executor_run(project_config, tmp_path):
    project_config.runtime.local_db_path = str(tmp_path / "test_app.db")
    
    class MockConfigService:
        def load(self, path):
            return project_config
            
    summary = PipelineExecutor(config_service=MockConfigService()).run("tests/samples/configs")

    assert summary.run_id is not None
    assert summary.project_id == "finance_etl"
    assert summary.error is None

    assert len(summary.canonical_results) > 0
    canonical = summary.canonical_results[0]
    
    assert canonical.table_name == "companies"
    assert canonical.error is None
    
    assert canonical.pipeline_result is not None
    pr = canonical.pipeline_result
    assert pr.discovered_count > 0
    assert pr.selected_count > 0
    assert pr.read_payload_count > 0
    
    assert pr.final_batch_payload is not None
    assert pr.final_batch_payload.frame is not None
    schema = pr.final_batch_payload.frame.collect_schema()
    assert len(list(schema.names())) > 0
            
    assert canonical.load_result is not None
    assert canonical.load_result.inserted_rows >= 0
    
    assert canonical.dlq_summary is not None
    assert canonical.dlq_summary.persisted_row_count >= 0
        
    assert len(summary.derived_results) > 0
    assert len(summary.semantic_results) > 0
