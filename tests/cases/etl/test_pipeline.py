from semantic_finance_etl.config.services.project_config_service import ProjectConfigService
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

config = ProjectConfigService().load("tests/samples/configs")
source = config.sources[0]

discoverer = FilesystemSourceDiscoverer()
selector = LatestModifiedSourceSelector()
grouper = SingleGroupSourceGrouper()
reader = SQLiteQuerySourceReader()

discovered = discoverer.discover(source)
print("Discovered:", len(discovered))

selected = selector.select(source, discovered)
print("Selected:", len(selected))
print("Selected paths:", [asset.path for asset in selected])

groups = grouper.group(source, selected)
print("Groups:", len(groups))
print("Group ids:", [group.group_id for group in groups])

if groups:
    read_payloads = reader.read_group(
        source_config=source,
        reader_config=source.reader,
        group=groups[0],
    )

    print("Read payload count:", len(read_payloads))

    for payload in read_payloads:
        print("Asset:", payload.asset.path)
        print("Rows:", len(payload.frame))
        print("Inferred schema:", payload.inferred_schema)
        print("Parse metadata:", payload.parse_metadata)
