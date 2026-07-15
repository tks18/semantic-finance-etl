from __future__ import annotations

import importlib
import importlib.util
import inspect
import pkgutil
import sys
from pathlib import Path
from types import ModuleType
from typing import Iterable

from semantic_finance_etl.contracts.hook import BaseHook


def _is_hook_class(obj: object) -> bool:
    return (
        inspect.isclass(obj)
        and issubclass(obj, BaseHook)
        and obj is not BaseHook
        and not inspect.isabstract(obj)
    )


def _discover_hook_classes_in_module(module: ModuleType) -> list[type[BaseHook]]:
    hook_classes: list[type[BaseHook]] = []

    for _, obj in inspect.getmembers(module, inspect.isclass):
        if _is_hook_class(obj):
            hook_classes.append(obj)

    return hook_classes


def _import_module_from_file(module_name: str, file_path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to create import spec for file: {file_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _load_modules_from_directory(directory: Path) -> list[ModuleType]:
    modules: list[ModuleType] = []

    if not directory.exists():
        return modules

    if not directory.is_dir():
        raise ValueError(f"Expected a directory path, got: {directory}")

    for py_file in sorted(directory.glob("*.py")):
        if py_file.name.startswith("_"):
            continue

        module_name = f"_semantic_finance_etl_user_hook_{py_file.stem}"
        module = _import_module_from_file(module_name, py_file)
        modules.append(module)

    return modules


def _load_modules_from_package(package_name: str) -> list[ModuleType]:
    modules: list[ModuleType] = []

    package = importlib.import_module(package_name)
    modules.append(package)

    if hasattr(package, "__path__"):
        for module_info in pkgutil.walk_packages(package.__path__, prefix=f"{package_name}."):
            submodule = importlib.import_module(module_info.name)
            modules.append(submodule)

    return modules


def discover_hook_classes(search_path: str) -> list[type[BaseHook]]:
    path_obj = Path(search_path)

    if path_obj.exists():
        modules = _load_modules_from_directory(path_obj)
    else:
        modules = _load_modules_from_package(search_path)

    discovered: list[type[BaseHook]] = []
    seen: set[tuple[str, str]] = set()

    for module in modules:
        for hook_class in _discover_hook_classes_in_module(module):
            key = (hook_class.__module__, hook_class.__name__)
            if key not in seen:
                seen.add(key)
                discovered.append(hook_class)

    return discovered


def load_hook_class_from_explicit_ref(module_name: str, class_name: str) -> type[BaseHook]:
    module = importlib.import_module(module_name)

    if not hasattr(module, class_name):
        raise ValueError(
            f"Module '{module_name}' does not define hook class '{class_name}'."
        )

    hook_class = getattr(module, class_name)

    if not _is_hook_class(hook_class):
        raise ValueError(
            f"'{module_name}.{class_name}' is not a valid concrete BaseHook subclass."
        )

    return hook_class
