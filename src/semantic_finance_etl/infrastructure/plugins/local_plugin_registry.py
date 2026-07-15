from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from semantic_finance_etl.contracts.hook import BaseHook
from semantic_finance_etl.domain.enums.hook_stage import HookStage
from semantic_finance_etl.infrastructure.plugins.hook_loader import discover_hook_classes


@dataclass(slots=True)
class HookRegistration:
    hook_name: str
    hook_class: type[BaseHook]
    module_path: str
    class_name: str
    stage: HookStage
    params_model: type[Any]


class LocalPluginRegistry:
    def __init__(self) -> None:
        self._hooks_by_name: dict[str, HookRegistration] = {}

    def register_hook(self, hook_class: type[BaseHook]) -> None:
        hook_name = getattr(hook_class, "hook_name", None)
        stage = getattr(hook_class, "stage", None)
        params_model = getattr(hook_class, "params_model", None)

        if not hook_name or not isinstance(hook_name, str):
            raise ValueError(f"Hook class '{hook_class.__name__}' must define a valid hook_name.")

        if stage is None or not isinstance(stage, HookStage):
            raise ValueError(f"Hook '{hook_name}' must define a valid HookStage.")

        if params_model is None:
            raise ValueError(f"Hook '{hook_name}' must define params_model.")

        if hook_name in self._hooks_by_name:
            existing = self._hooks_by_name[hook_name]
            raise ValueError(
                f"Duplicate hook_name '{hook_name}' found in "
                f"'{existing.module_path}.{existing.class_name}' and "
                f"'{hook_class.__module__}.{hook_class.__name__}'."
            )

        self._hooks_by_name[hook_name] = HookRegistration(
            hook_name=hook_name,
            hook_class=hook_class,
            module_path=hook_class.__module__,
            class_name=hook_class.__name__,
            stage=stage,
            params_model=params_model,
        )

    def register_from_search_path(self, search_path: str) -> None:
        for hook_class in discover_hook_classes(search_path):
            self.register_hook(hook_class)

    def register_from_search_paths(self, search_paths: list[str]) -> None:
        for search_path in search_paths:
            self.register_from_search_path(search_path)

    def has_hook(self, hook_name: str) -> bool:
        return hook_name in self._hooks_by_name

    def get_hook(self, hook_name: str) -> HookRegistration:
        if hook_name not in self._hooks_by_name:
            available = ", ".join(sorted(self._hooks_by_name.keys())) or "<none>"
            raise ValueError(
                f"Hook '{hook_name}' is not registered. Available hooks: {available}"
            )
        return self._hooks_by_name[hook_name]

    def list_hooks(self) -> list[HookRegistration]:
        return [
            self._hooks_by_name[name]
            for name in sorted(self._hooks_by_name.keys())
        ]
