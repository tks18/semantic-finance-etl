"""
Pytest tests for reader pipeline: discovery → selection → grouping → reading (LazyFrame output).
"""
import polars as pl
from semantic_finance_etl.config.models.project_config import ProjectConfig
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


def test_reader_pipeline(project_config: ProjectConfig):
    source = project_config.sources[0]

    discoverer = FilesystemSourceDiscoverer()
    selector = LatestModifiedSourceSelector()
    grouper = SingleGroupSourceGrouper()
    reader = SQLiteQuerySourceReader()

    discovered = discoverer.discover(source)
    assert len(discovered) > 0

    selected = selector.select(source, discovered)
    assert len(selected) > 0
    assert selected[0].path.endswith("companies.db")

    groups = grouper.group(source, selected)
    assert len(groups) > 0
    
    read_payloads = reader.read_group(
        source_config=source,
        reader_config=source.reader,
        group=groups[0],
    )

    assert len(read_payloads) > 0

    for payload in read_payloads:
        assert payload.asset.path.endswith("companies.db")
        assert isinstance(payload.frame, pl.LazyFrame)
        df = payload.frame.collect()
        assert len(df) > 0
        assert payload.data_schema is not None
