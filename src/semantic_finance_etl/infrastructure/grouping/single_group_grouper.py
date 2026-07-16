from __future__ import annotations

from semantic_finance_etl.config.models.source_config import SourceConfig
from semantic_finance_etl.contracts.source_grouper import SourceAssetGroup, SourceGrouper
from semantic_finance_etl.domain.models.hook_payloads import DiscoveredAsset


class SingleGroupSourceGrouper(SourceGrouper[None]):
    grouper_name = "single_group"

    def group(
        self,
        source_config: SourceConfig,
        selected_assets: list[DiscoveredAsset],
        params: None = None,
    ) -> list[SourceAssetGroup]:
        if not selected_assets:
            return []

        return [
            SourceAssetGroup(
                group_id=f"{source_config.source_id}__single_group",
                assets=selected_assets,
                metadata={
                    "source_id": source_config.source_id,
                    "grouping_strategy": self.grouper_name,
                    "asset_count": len(selected_assets),
                },
            )
        ]
