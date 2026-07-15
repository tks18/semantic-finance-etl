from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar, Generic, TypeVar

from pydantic import BaseModel

from semantic_finance_etl.domain.enums.hook_stage import HookStage
from semantic_finance_etl.domain.models.hook_payloads import ExecutionContext
from semantic_finance_etl.domain.models.hook_results import HookExecutionResult

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")
ParamsT = TypeVar("ParamsT", bound=BaseModel)


class BaseHook(ABC, Generic[InputT, OutputT, ParamsT]):
    hook_name: ClassVar[str]
    stage: ClassVar[HookStage]
    params_model: ClassVar[type[ParamsT]]

    supported_table_names: ClassVar[set[str]] = set()
    supported_table_kinds: ClassVar[set[str]] = set()

    required_columns: ClassVar[set[str]] = set()
    optional_columns: ClassVar[set[str]] = set()
    produced_columns: ClassVar[set[str]] = set()

    preserves_schema: ClassVar[bool] = True
    may_change_row_count: ClassVar[bool] = False

    @abstractmethod
    def execute(
        self,
        context: ExecutionContext,
        payload: InputT,
        params: ParamsT,
    ) -> HookExecutionResult[OutputT]:
        raise NotImplementedError

    @classmethod
    def validate_stage(cls, expected_stage: HookStage) -> None:
        if cls.stage != expected_stage:
            raise ValueError(
                f"Hook '{cls.hook_name}' is declared for stage '{cls.stage.value}' "
                f"but was bound to '{expected_stage.value}'."
            )

    @classmethod
    def supports_table_name(cls, table_name: str) -> bool:
        return not cls.supported_table_names or table_name in cls.supported_table_names

    @classmethod
    def supports_table_kind(cls, table_kind: str) -> bool:
        return not cls.supported_table_kinds or table_kind in cls.supported_table_kinds


class SourceHook(BaseHook[InputT, OutputT, ParamsT], ABC):
    pass


class TableHook(BaseHook[InputT, OutputT, ParamsT], ABC):
    pass


class DerivedTableHook(BaseHook[InputT, OutputT, ParamsT], ABC):
    pass


class SemanticHook(BaseHook[InputT, OutputT, ParamsT], ABC):
    pass
