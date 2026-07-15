from __future__ import annotations

from dataclasses import dataclass

from semantic_finance_etl.config.models.transform_config import (
    ExplicitHookReference,
    HookBindingConfig,
)
from semantic_finance_etl.contracts.hook import BaseHook
from semantic_finance_etl.domain.enums.hook_stage import HookStage
from semantic_finance_etl.infrastructure.plugins.hook_loader import (
    load_hook_class_from_explicit_ref,
)
from semantic_finance_etl.infrastructure.plugins.local_plugin_registry import (
    HookRegistration,
    LocalPluginRegistry,
)


@dataclass(slots=True)
class ResolvedHookBinding:
    hook_name: str
    stage: HookStage
    hook_class: type[BaseHook]
    params: object
    binding: HookBindingConfig
    module_path: str
    class_name: str

    def create_instance(self) -> BaseHook:
        return self.hook_class()


class HookBindingResolver:
    def __init__(self, registry: LocalPluginRegistry) -> None:
        self._registry = registry

    def resolve_bindings_for_stage(
        self,
        stage: HookStage,
        bindings: list[HookBindingConfig],
    ) -> list[ResolvedHookBinding]:
        resolved_bindings: list[ResolvedHookBinding] = []

        for binding in bindings:
            if not binding.enabled:
                continue

            resolved_bindings.append(self.resolve_binding(stage=stage, binding=binding))

        return sorted(
            resolved_bindings,
            key=lambda item: (item.binding.order, item.hook_name),
        )

    def resolve_binding(
        self,
        stage: HookStage,
        binding: HookBindingConfig,
    ) -> ResolvedHookBinding:
        if binding.hook:
            registration = self._registry.get_hook(binding.hook)
            hook_class = registration.hook_class
            module_path = registration.module_path
            class_name = registration.class_name
            hook_name = registration.hook_name
        elif binding.hook_ref:
            hook_class = self._load_hook_from_explicit_ref(binding.hook_ref)
            hook_name = hook_class.hook_name
            module_path = hook_class.__module__
            class_name = hook_class.__name__
        else:
            raise ValueError("Hook binding must define either 'hook' or 'hook_ref'.")

        hook_class.validate_stage(stage)

        params = hook_class.params_model.model_validate(binding.params)

        return ResolvedHookBinding(
            hook_name=hook_name,
            stage=stage,
            hook_class=hook_class,
            params=params,
            binding=binding,
            module_path=module_path,
            class_name=class_name,
        )

    def _load_hook_from_explicit_ref(
        self,
        hook_ref: ExplicitHookReference,
    ) -> type[BaseHook]:
        return load_hook_class_from_explicit_ref(
            module_name=hook_ref.module,
            class_name=hook_ref.class_name,
        )
