from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from semantic_finance_etl.domain.enums.fail_behavior import FailBehavior


class ExplicitHookReference(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    module: str
    class_name: str = Field(alias="class")


class HookBindingConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    hook: str | None = None
    hook_ref: ExplicitHookReference | None = None

    order: int = 100
    enabled: bool = True
    params: dict[str, Any] = Field(default_factory=dict)

    fail_behavior: FailBehavior = FailBehavior.FAIL_RUN
    timeout_seconds: int | None = None
    retry_count: int = 0

    @model_validator(mode="after")
    def validate_reference(self) -> "HookBindingConfig":
        has_hook = self.hook is not None and self.hook.strip() != ""
        has_hook_ref = self.hook_ref is not None

        if has_hook == has_hook_ref:
            raise ValueError(
                "Exactly one of 'hook' or 'hook_ref' must be provided."
            )

        if self.timeout_seconds is not None and self.timeout_seconds <= 0:
            raise ValueError("'timeout_seconds' must be > 0 when provided.")

        if self.retry_count < 0:
            raise ValueError("'retry_count' cannot be negative.")

        return self


class StageHookBindings(BaseModel):
    post_read: list[HookBindingConfig] = Field(default_factory=list)
    pre_append: list[HookBindingConfig] = Field(default_factory=list)
    post_append: list[HookBindingConfig] = Field(default_factory=list)
    pre_validate: list[HookBindingConfig] = Field(default_factory=list)
    post_validate: list[HookBindingConfig] = Field(default_factory=list)
    pre_load: list[HookBindingConfig] = Field(default_factory=list)
    post_load: list[HookBindingConfig] = Field(default_factory=list)
    pre_derive: list[HookBindingConfig] = Field(default_factory=list)
    post_derive: list[HookBindingConfig] = Field(default_factory=list)
    pre_semantic: list[HookBindingConfig] = Field(default_factory=list)
    post_semantic: list[HookBindingConfig] = Field(default_factory=list)

    def as_dict(self) -> dict[str, list[HookBindingConfig]]:
        return {
            "post_read": self.post_read,
            "pre_append": self.pre_append,
            "post_append": self.post_append,
            "pre_validate": self.pre_validate,
            "post_validate": self.post_validate,
            "pre_load": self.pre_load,
            "post_load": self.post_load,
            "pre_derive": self.pre_derive,
            "post_derive": self.post_derive,
            "pre_semantic": self.pre_semantic,
            "post_semantic": self.post_semantic,
        }

    def has_any_hooks(self) -> bool:
        return any(len(bindings) > 0 for bindings in self.as_dict().values())
