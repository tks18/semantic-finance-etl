from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from semantic_finance_etl.config.models.source_config import ReaderConfig, SourceConfig
from semantic_finance_etl.contracts.source_grouper import SourceAssetGroup
from semantic_finance_etl.domain.models.hook_payloads import DiscoveredAsset, ReadPayload

ReaderParamsT = TypeVar("ReaderParamsT")


class SourceReader(ABC, Generic[ReaderParamsT]):
    reader_name: str

    @abstractmethod
    def read_asset(
        self,
        source_config: SourceConfig,
        reader_config: ReaderConfig,
        asset: DiscoveredAsset,
        params: ReaderParamsT | None = None,
    ) -> ReadPayload:
        raise NotImplementedError

    def read_group(
        self,
        source_config: SourceConfig,
        reader_config: ReaderConfig,
        group: SourceAssetGroup,
        params: ReaderParamsT | None = None,
    ) -> list[ReadPayload]:
        return [
            self.read_asset(
                source_config=source_config,
                reader_config=reader_config,
                asset=asset,
                params=params,
            )
            for asset in group.assets
        ]
