from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from semantic_finance_etl.config.models.source_config import SourceConfig
from semantic_finance_etl.domain.models.hook_payloads import DiscoveredAsset

SelectorParamsT = TypeVar("SelectorParamsT")


class SourceSelector(ABC, Generic[SelectorParamsT]):
    selector_name: str

    @abstractmethod
    def select(
        self,
        source_config: SourceConfig,
        discovered_assets: list[DiscoveredAsset],
        params: SelectorParamsT | None = None,
    ) -> list[DiscoveredAsset]:
        raise NotImplementedError
