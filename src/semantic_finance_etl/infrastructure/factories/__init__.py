from __future__ import annotations

from semantic_finance_etl.config.models.source_config import SourceConfig
from semantic_finance_etl.contracts.source_discoverer import SourceDiscoverer
from semantic_finance_etl.contracts.source_grouper import SourceGrouper
from semantic_finance_etl.contracts.source_reader import SourceReader
from semantic_finance_etl.contracts.source_selector import SourceSelector
from semantic_finance_etl.infrastructure.discovery.filesystem_discoverer import (
    FilesystemSourceDiscoverer,
)
from semantic_finance_etl.infrastructure.grouping.single_group_grouper import (
    SingleGroupSourceGrouper,
)
from semantic_finance_etl.infrastructure.readers.sqlite_query_reader import (
    SQLiteQuerySourceReader,
)
from semantic_finance_etl.infrastructure.selection.latest_modified_selector import (
    LatestModifiedSourceSelector,
)


class SourceComponentFactory:
    def create_discoverer(self, source_config: SourceConfig) -> SourceDiscoverer:
        if source_config.discoverer == "filesystem":
            return FilesystemSourceDiscoverer()

        raise ValueError(
            f"Unsupported discoverer '{source_config.discoverer}' for source "
            f"'{source_config.source_id}'."
        )

    def create_selector(self, source_config: SourceConfig) -> SourceSelector:
        if source_config.selector == "latest_modified":
            return LatestModifiedSourceSelector()

        raise ValueError(
            f"Unsupported selector '{source_config.selector}' for source "
            f"'{source_config.source_id}'."
        )

    def create_grouper(self, source_config: SourceConfig) -> SourceGrouper:
        if source_config.grouper == "single_group":
            return SingleGroupSourceGrouper()

        raise ValueError(
            f"Unsupported grouper '{source_config.grouper}' for source "
            f"'{source_config.source_id}'."
        )

    def create_reader(self, source_config: SourceConfig) -> SourceReader:
        if source_config.reader.type == "sqlite_query":
            return SQLiteQuerySourceReader()

        raise ValueError(
            f"Unsupported reader type '{source_config.reader.type}' for source "
            f"'{source_config.source_id}'."
        )
