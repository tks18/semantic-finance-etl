from semantic_finance_etl.config.services.project_config_service import ProjectConfigService
from semantic_finance_etl.domain.enums.hook_stage import HookStage
from semantic_finance_etl.etl.hooks.hook_binding_resolver import HookBindingResolver
from semantic_finance_etl.infrastructure.plugins.local_plugin_registry import LocalPluginRegistry

config = ProjectConfigService().load("tests/samples/configs")

registry = LocalPluginRegistry()
registry.register_from_search_paths(config.runtime.hook_search_paths)

resolver = HookBindingResolver(registry=registry)

table = config.tables[0]
resolved = resolver.resolve_bindings_for_stage(
    stage=HookStage.PRE_LOAD,
    bindings=table.hooks.pre_load,
)

for item in resolved:
    print(
        {
            "hook_name": item.hook_name,
            "stage": item.stage.value,
            "params": item.params.model_dump(),
            "module_path": item.module_path,
            "class_name": item.class_name,
        }
    )
