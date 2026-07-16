"""
Pytest test for full pipeline executor run.
"""
from semantic_finance_etl.etl.orchestration.pipeline_executor import PipelineExecutor
import pytest

def test_pipeline_executor_run():
    summary = PipelineExecutor().run("tests/samples/configs")

    assert summary.run_id is not None
    assert summary.project_id == "finance_etl"
    assert summary.error is None

    assert len(summary.canonical_results) > 0
    canonical = summary.canonical_results[0]
    
    assert canonical.table_name == "companies"
    assert canonical.error is None
    
    if canonical.pipeline_result:
        pr = canonical.pipeline_result
        assert pr.discovered_count > 0
        assert pr.selected_count > 0
        assert pr.read_payload_count > 0
        
        assert pr.final_batch_payload is not None
        if pr.final_batch_payload.frame is not None:
            schema = pr.final_batch_payload.frame.collect_schema()
            assert len(list(schema.names())) > 0
            
    if canonical.load_result:
        assert canonical.load_result.inserted_rows >= 0
    
    if canonical.dlq_summary:
        assert canonical.dlq_summary.persisted_row_count >= 0
        
    assert len(summary.derived_results) > 0
    assert len(summary.semantic_results) > 0
