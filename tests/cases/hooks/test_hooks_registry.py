from semantic_finance_etl.config.services.project_config_service import ProjectConfigService
from semantic_finance_etl.infrastructure.plugins.local_plugin_registry import LocalPluginRegistry

config = ProjectConfigService().load("tests/samples/configs")

registry = LocalPluginRegistry()
registry.register_from_search_paths(config.runtime.hook_search_paths)

for hook in registry.list_hooks():
    print(
        {
            "hook_name": hook.hook_name,
            "stage": hook.stage.value,
            "module_path": hook.module_path,
            "class_name": hook.class_name,
        }
    )
