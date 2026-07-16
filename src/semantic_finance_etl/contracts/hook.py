from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar, Generic, TypeVar

from pydantic import BaseModel

from semantic_finance_etl.domain.enums.hook_stage import HookStage
from semantic_finance_etl.domain.models.data_schema import DataSchema
from semantic_finance_etl.domain.models.frame_contracts import FrameContract
from semantic_finance_etl.domain.models.hook_payloads import ExecutionContext
from semantic_finance_etl.domain.models.hook_results import HookExecutionResult

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")
ParamsT = TypeVar("ParamsT", bound=BaseModel)


class BaseHook(ABC, Generic[InputT, OutputT, ParamsT]):
    """Base class for all ETL hooks.

    Class-level attributes declare the hook's identity, schema expectations,
    and frame contract so the runner can validate before execution.
    All hooks operate on ``pl.LazyFrame``-bearing payloads.
    """

    hook_name: ClassVar[str]
    stage: ClassVar[HookStage]
    params_model: ClassVar[type[ParamsT]]

    # Optional scope guards — empty sets mean "accept all".
    supported_table_names: ClassVar[set[str]] = set()
    supported_table_kinds: ClassVar[set[str]] = set()

    # --- Schema declarations ---
    # Declare which columns this hook requires and which it produces so the
    # runner can check contracts before any data is materialized.
    required_columns: ClassVar[set[str]] = set()
    optional_columns: ClassVar[set[str]] = set()
    produced_columns: ClassVar[set[str]] = set()

    # Typed schema snapshots (optional — set when a hook has explicit contracts).
    input_schema: ClassVar[DataSchema | None] = None
    output_schema: ClassVar[DataSchema | None] = None

    # FrameContract carries schema_mutation, cardinality, and materialization policy.
    frame_contract: ClassVar[FrameContract | None] = None

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

    @classmethod
    def validate_frame_contract(cls, input_schema: DataSchema | None = None) -> None:
        """Validate that the given input schema satisfies this hook's frame contract.

        Called by the hook runner before execution when a frame contract is declared.
        No-ops when ``frame_contract`` is ``None``.
        """
        if cls.frame_contract is None:
            return
        cls.frame_contract.validate_input_schema(input_schema)

    @classmethod
    def describe(cls) -> dict[str, object]:
        """Return a summary dict for registry listing / UI display."""
        return {
            "hook_name": cls.hook_name,
            "stage": cls.stage.value,
            "required_columns": sorted(cls.required_columns),
            "optional_columns": sorted(cls.optional_columns),
            "produced_columns": sorted(cls.produced_columns),
            "has_input_schema": cls.input_schema is not None,
            "has_output_schema": cls.output_schema is not None,
            "has_frame_contract": cls.frame_contract is not None,
        }


class SourceHook(BaseHook[InputT, OutputT, ParamsT], ABC):
    """Hook that operates on ``ReadPayload`` at the ``post_read`` stage."""


class TableHook(BaseHook[InputT, OutputT, ParamsT], ABC):
    """Hook that operates on ``BatchPayload`` at table-level stages."""


class DerivedTableHook(BaseHook[InputT, OutputT, ParamsT], ABC):
    """Hook that builds derived tables from ``DerivedBuildPayload``."""


class SemanticHook(BaseHook[InputT, OutputT, ParamsT], ABC):
    """Hook that operates on ``SemanticProjectionPayload``."""
