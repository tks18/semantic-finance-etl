from __future__ import annotations

from pathlib import Path
from typing import Any

from semantic_finance_etl.config.loaders.yaml_loader import (
    list_yaml_files,
    load_yaml_file,
    load_yaml_file_if_exists,
)
from semantic_finance_etl.config.models.project_config import ProjectConfig


def _normalize_runtime_payload(raw_runtime_data: dict[str, Any]) -> dict[str, Any]:
    if not raw_runtime_data:
        return {}

    if "runtime" in raw_runtime_data and isinstance(raw_runtime_data["runtime"], dict):
        return raw_runtime_data["runtime"]

    return raw_runtime_data


def _expand_config_items(
    file_payload: dict[str, Any],
    plural_key: str,
) -> list[dict[str, Any]]:
    """
    Supports both:
    1. a single config object in a file
    2. a wrapped list, e.g. { "sources": [ ... ] }
    """
    if not file_payload:
        return []

    if plural_key in file_payload:
        items = file_payload[plural_key]
        if not isinstance(items, list):
            raise ValueError(
                f"Expected '{plural_key}' to contain a list, got {type(items).__name__}."
            )

        for item in items:
            if not isinstance(item, dict):
                raise ValueError(
                    f"Expected each entry inside '{plural_key}' to be a mapping/object."
                )

        return items

    return [file_payload]


def _load_split_config_items(
    directory: Path,
    plural_key: str,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []

    for yaml_file in list_yaml_files(directory):
        payload = load_yaml_file(yaml_file)
        items.extend(_expand_config_items(payload, plural_key=plural_key))

    return items


def load_project_config(config_root: str | Path) -> ProjectConfig:
    root = Path(config_root)

    if not root.exists():
        raise FileNotFoundError(f"Config directory does not exist: {root}")

    if not root.is_dir():
        raise ValueError(f"Expected config_root to be a directory: {root}")

    project_file = root / "project.yaml"
    project_data = load_yaml_file(project_file)

    runtime_data = _normalize_runtime_payload(
        load_yaml_file_if_exists(root / "runtime.yaml")
    )

    split_sources = _load_split_config_items(root / "sources", plural_key="sources")
    split_tables = _load_split_config_items(root / "tables", plural_key="tables")
    split_semantics = _load_split_config_items(root / "semantics", plural_key="semantics")

    inline_sources = project_data.get("sources", [])
    inline_tables = project_data.get("tables", [])
    inline_semantics = project_data.get("semantics", [])

    if not isinstance(inline_sources, list):
        raise ValueError("Expected 'sources' in project.yaml to be a list.")
    if not isinstance(inline_tables, list):
        raise ValueError("Expected 'tables' in project.yaml to be a list.")
    if not isinstance(inline_semantics, list):
        raise ValueError("Expected 'semantics' in project.yaml to be a list.")

    merged_data = dict(project_data)

    merged_runtime = dict(project_data.get("runtime", {}))
    merged_runtime.update(runtime_data)

    merged_data["runtime"] = merged_runtime
    merged_data["sources"] = [*inline_sources, *split_sources]
    merged_data["tables"] = [*inline_tables, *split_tables]
    merged_data["semantics"] = [*inline_semantics, *split_semantics]

    return ProjectConfig.model_validate(merged_data)
