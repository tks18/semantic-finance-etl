from __future__ import annotations

from semantic_finance_etl.config.models.source_config import SourceConfig
from semantic_finance_etl.contracts.source_selector import SourceSelector
from semantic_finance_etl.domain.models.hook_payloads import DiscoveredAsset


class LatestModifiedSourceSelector(SourceSelector[None]):
    selector_name = "latest_modified"

    def select(
        self,
        source_config: SourceConfig,
        discovered_assets: list[DiscoveredAsset],
        params: None = None,
    ) -> list[DiscoveredAsset]:
        if not discovered_assets:
            return []

        sorted_assets = sorted(
            discovered_assets,
            key=lambda asset: (
                asset.modified_at_utc is not None,
                asset.modified_at_utc,
                asset.path,
            ),
            reverse=True,
        )

        return [sorted_assets[0]]
