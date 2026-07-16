"""
Pytest test for hook binding resolver.
"""
from semantic_finance_etl.domain.enums.hook_stage import HookStage
from semantic_finance_etl.etl.hooks.hook_binding_resolver import HookBindingResolver
from semantic_finance_etl.infrastructure.plugins.local_plugin_registry import LocalPluginRegistry

def test_hooks_resolver(project_config):
    registry = LocalPluginRegistry()
    registry.register_from_search_paths(project_config.runtime.hook_search_paths)
    
    resolver = HookBindingResolver(registry=registry)
    
    table = project_config.tables[0]
    resolved = resolver.resolve_bindings_for_stage(
        stage=HookStage.POST_APPEND,
        bindings=table.hooks.post_append,
    )
    
    assert len(resolved) == 1
    item = resolved[0]
    
    assert item.hook_name == "clean_companies_data"
    assert item.stage == HookStage.POST_APPEND
    assert item.class_name == "CleanCompaniesDataHook"
