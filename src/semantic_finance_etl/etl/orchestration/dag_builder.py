from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field

from semantic_finance_etl.config.models.table_config import TableConfig
from semantic_finance_etl.domain.enums.table_kind import TableKind


@dataclass(slots=True)
class TableNode:
    """A single node in the dependency DAG."""

    table_name: str
    table_kind: TableKind
    depends_on: list[str]


@dataclass(slots=True)
class BuildPlan:
    """The resolved topological build order for all tables.

    ``canonical_tables`` is the ordered list of ingestion tables.
    ``derived_tables`` is the topologically ordered list of derived tables
    — each entry guaranteed to come after all its dependencies.
    """

    canonical_tables: list[str] = field(default_factory=list)
    derived_tables: list[str] = field(default_factory=list)

    @property
    def all_tables_in_order(self) -> list[str]:
        """Canonical tables first, then derived in dependency order."""
        return self.canonical_tables + self.derived_tables


class DAGBuilder:
    """Builds and resolves a topological dependency graph for table configs.

    Only ``DERIVED`` tables participate in the DAG resolution.
    Canonical tables are always processed first in declaration order.

    Usage::

        plan = DAGBuilder().build(project_config.tables)
        for table_name in plan.all_tables_in_order:
            ...
    """

    def build(self, tables: list[TableConfig]) -> BuildPlan:
        canonical = [t for t in tables if t.table_kind == TableKind.CANONICAL]
        derived = [t for t in tables if t.table_kind == TableKind.DERIVED]

        ordered_derived = self._topological_sort(derived)

        return BuildPlan(
            canonical_tables=[t.table_name for t in canonical],
            derived_tables=ordered_derived,
        )

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _topological_sort(self, derived: list[TableConfig]) -> list[str]:
        """Kahn's algorithm — raises on cycles."""
        if not derived:
            return []

        node_map: dict[str, TableConfig] = {t.table_name: t for t in derived}

        # in-degree counts for derived tables only.
        in_degree: dict[str, int] = {t.table_name: 0 for t in derived}
        # adjacents[A] = tables that depend on A
        adjacents: dict[str, list[str]] = defaultdict(list)

        for table in derived:
            for dep in table.depends_on:
                if dep in node_map:
                    # dep → table edge
                    in_degree[table.table_name] += 1
                    adjacents[dep].append(table.table_name)
                # canonical deps are always satisfied — don't count them

        queue: deque[str] = deque(
            name for name, deg in in_degree.items() if deg == 0
        )
        ordered: list[str] = []

        while queue:
            name = queue.popleft()
            ordered.append(name)
            for dependent in adjacents[name]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        if len(ordered) != len(derived):
            cycle_nodes = [n for n, d in in_degree.items() if d > 0]
            raise ValueError(
                f"Circular dependency detected among derived tables: {cycle_nodes}"
            )

        return ordered
