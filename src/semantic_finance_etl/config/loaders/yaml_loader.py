from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_yaml_file(path: str | Path) -> dict[str, Any]:
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"YAML file not found: {file_path}")

    if not file_path.is_file():
        raise ValueError(f"Expected a file but found something else: {file_path}")

    with file_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    if not isinstance(data, dict):
        raise ValueError(
            f"Expected YAML root to be a mapping/object in file: {file_path}"
        )

    return data


def load_yaml_file_if_exists(path: str | Path) -> dict[str, Any]:
    file_path = Path(path)

    if not file_path.exists():
        return {}

    return load_yaml_file(file_path)


def list_yaml_files(directory: str | Path) -> list[Path]:
    dir_path = Path(directory)

    if not dir_path.exists():
        return []

    if not dir_path.is_dir():
        raise ValueError(f"Expected a directory but found something else: {dir_path}")

    files = [
        path
        for path in dir_path.iterdir()
        if path.is_file() and path.suffix.lower() in {".yaml", ".yml"}
    ]

    return sorted(files, key=lambda p: p.name.lower())
