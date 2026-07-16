"""
pytest tests - Orchestration layer (DAGBuilder, PipelineExecutor)
"""
from __future__ import annotations

import pytest

from semantic_finance_etl.config.models.table_config import TableConfig, BuildConfig
from semantic_finance_etl.domain.enums.table_kind import TableKind
from semantic_finance_etl.etl.orchestration.dag_builder import DAGBuilder


class TestDAGBuilder:
    def test_separates_canonical_and_derived(self):
        canonical1 = TableConfig(table_name="t1", table_kind=TableKind.CANONICAL)
        canonical2 = TableConfig(table_name="t2", table_kind=TableKind.CANONICAL)
        derived1 = TableConfig(
            table_name="d1", table_kind=TableKind.DERIVED, 
            depends_on=["t1"], build=BuildConfig()
        )
        
        plan = DAGBuilder().build([canonical1, canonical2, derived1])
        
        assert plan.canonical_tables == ["t1", "t2"]
        assert plan.derived_tables == ["d1"]
        assert plan.all_tables_in_order == ["t1", "t2", "d1"]

    def test_resolves_derived_dependency_order(self):
        # t1 -> d1 -> d2
        #       d3 -> d2
        t1 = TableConfig(table_name="t1", table_kind=TableKind.CANONICAL)
        d1 = TableConfig(
            table_name="d1", table_kind=TableKind.DERIVED, 
            depends_on=["t1"], build=BuildConfig()
        )
        d2 = TableConfig(
            table_name="d2", table_kind=TableKind.DERIVED, 
            depends_on=["d1", "d3"], build=BuildConfig()
        )
        d3 = TableConfig(
            table_name="d3", table_kind=TableKind.DERIVED, 
            depends_on=["t1"], build=BuildConfig()
        )
        
        plan = DAGBuilder().build([t1, d2, d1, d3])
        
        assert plan.canonical_tables == ["t1"]
        # d1 and d3 have no derived dependencies (d1 depends on canonical t1)
        # d2 depends on d1 and d3. So d2 must be last in derived.
        assert plan.derived_tables[-1] == "d2"
        assert set(plan.derived_tables[:2]) == {"d1", "d3"}

    def test_detects_cycles(self):
        a = TableConfig(
            table_name="a", table_kind=TableKind.DERIVED, 
            depends_on=["b"], build=BuildConfig()
        )
        b = TableConfig(
            table_name="b", table_kind=TableKind.DERIVED, 
            depends_on=["a"], build=BuildConfig()
        )
        
        with pytest.raises(ValueError) as excinfo:
            DAGBuilder().build([a, b])
            
        assert "Circular dependency detected" in str(excinfo.value)
        assert "'a'" in str(excinfo.value)
        assert "'b'" in str(excinfo.value)
