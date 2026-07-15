from semantic_finance_etl.config.services.project_config_service import ProjectConfigService
from semantic_finance_etl.domain.models.runtime_table_definition import RuntimeTableDefinition
from semantic_finance_etl.etl.loading.load_service import LoadService
from semantic_finance_etl.etl.orchestration.pipeline_executor import PipelineExecutor
from semantic_finance_etl.etl.validation.validation_service import ValidationService

config = ProjectConfigService().load("tests/samples/configs")
summary = PipelineExecutor().run("tests/samples/configs")

result = summary.pipeline_results[0]
table_config = config.tables[0]
runtime_table = RuntimeTableDefinition.from_table_config(table_config)

validation_service = ValidationService()
validated_payload = validation_service.validate_batch(
    batch_payload=result.final_batch_payload,
    runtime_table=runtime_table,
)

print("Validation summary:")
print(validated_payload.validation_summary)

load_service = LoadService(config.runtime)
load_result = load_service.load(
    validated_payload=validated_payload,
    runtime_table=runtime_table,
)

print("Load result:")
print(load_result)
