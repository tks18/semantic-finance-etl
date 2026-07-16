from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from semantic_finance_etl.config.models.source_config import SourceConfig
from semantic_finance_etl.domain.models.hook_payloads import DiscoveredAsset

DiscoveryParamsT = TypeVar("DiscoveryParamsT")


class SourceDiscoverer(ABC, Generic[DiscoveryParamsT]):
    discoverer_name: str

    @abstractmethod
    def discover(
        self,
        source_config: SourceConfig,
        params: DiscoveryParamsT | None = None,
    ) -> list[DiscoveredAsset]:
        raise NotImplementedError
