"""
Pytest test for hook registry.
"""
from semantic_finance_etl.infrastructure.plugins.local_plugin_registry import LocalPluginRegistry

def test_hooks_registry(project_config):
    registry = LocalPluginRegistry()
    registry.register_from_search_paths(project_config.runtime.hook_search_paths)
    
    hooks = registry.list_hooks()
    assert len(hooks) > 0
    
    hook_names = [h.hook_name for h in hooks]
    assert "clean_companies_data" in hook_names
    assert "build_industry_stats" in hook_names
    assert "build_country_industry_summary" in hook_names
