from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Generic, TypeVar

from semantic_finance_etl.config.models.source_config import SourceConfig
from semantic_finance_etl.domain.models.hook_payloads import DiscoveredAsset

GrouperParamsT = TypeVar("GrouperParamsT")


@dataclass(slots=True)
class SourceAssetGroup:
    group_id: str
    assets: list[DiscoveredAsset] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class SourceGrouper(ABC, Generic[GrouperParamsT]):
    grouper_name: str

    @abstractmethod
    def group(
        self,
        source_config: SourceConfig,
        selected_assets: list[DiscoveredAsset],
        params: GrouperParamsT | None = None,
    ) -> list[SourceAssetGroup]:
        raise NotImplementedError
