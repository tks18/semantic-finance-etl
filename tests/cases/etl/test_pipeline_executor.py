from semantic_finance_etl.etl.orchestration.pipeline_executor import PipelineExecutor

summary = PipelineExecutor().run("tests/samples/configs")

print("Run ID:", summary.run_id)
print("Pipeline result count:", len(summary.pipeline_results))

for result in summary.pipeline_results:
    print("=" * 80)
    print("Source:", result.source_id)
    print("Table:", result.table_name)
    print("Discovered:", result.discovered_count)
    print("Selected:", result.selected_count)
    print("Groups:", result.group_count)
    print("Read payloads:", result.read_payload_count)

    if result.final_batch_payload is not None:
        frame = result.final_batch_payload.frame
        row_count = len(frame) if isinstance(frame, list) else None
        print("Final row count:", row_count)
        print("Inferred schema:", result.final_batch_payload.inferred_schema)
        print("Batch metadata:", result.final_batch_payload.batch_metadata)

    print("Post-read hook executions:", len(result.post_read_records))
    print("Post-append hook executions:", len(result.post_append_records))
    print("Pre-load hook executions:", len(result.pre_load_records))
