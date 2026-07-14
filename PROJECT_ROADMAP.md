# `semantic-finance-ETL` v2 Design Document
## Local-first, privacy-preserving, configuration-driven finance ETL and semantic analytics engine

## 1. Executive Design Decision

`semantic-finance-ETL` should be designed as a **generic ETL engine**, not as a hardcoded “personal finance app with a few pipelines.”

That means:

- **sources are dynamic**
- **tables are dynamic**
- **schemas are dynamic**
- **transformations are dynamic**
- **semantic sentence generation is dynamic**
- **analytical/derived tables are first-class**
- **UI is only a configuration and execution shell**
- **all behavior is driven by config + plugin registry + runtime model generation**

The engine itself should only know **how to**:

1. discover data
2. read data
3. normalize data
4. transform data
5. validate data via Pydantic
6. create/update SQLite schema
7. load data idempotently
8. build semantic text
9. create embeddings locally
10. expose results to Power BI and local AI agents

So the correct mental model is:

```text
semantic-finance-ETL = configurable local ETL runtime
not
semantic-finance-ETL = hardcoded finance tables application
```

---

## 2. Your Requested Changes, Converted into Design Decisions

## 2.1 Multi-source ingestion
The system must support:

- `xlsx`
- `xlsm`
- `csv`
- `tsv`
- `json`
- `jsonl`
- `parquet`
- `sqlite`
- other local SQL sources
  - DuckDB
  - PostgreSQL on localhost
  - MySQL on localhost
  - SQL Server on localhost
  - any ODBC/JDBC-reachable local DB, if configured
- future extension:
  - XML
  - fixed-width text
  - Access exports
  - zipped local archives

**Design decision:** all source reading happens through a **plugin-based source adapter layer**.

---

## 2.2 Flexible source discovery and selection
You explicitly want combinations like:

- select **latest modified file only**
- select **latest created file only**
- select **all files**
- select files by pattern
- select files recursively
- select SQLite backup DBs from folder, then query only the selected DB(s)
- append first then transform
- transform first then append

**Design decision:** split this into separate plugin concepts instead of one giant reader:

- `SourceDiscoverer` → finds candidate files or DBs
- `SourceSelector` → chooses which candidates to use
- `SourceGrouper` → groups candidates into one logical batch
- `SourceReader` → reads the actual file/DB/query
- `CombineStrategy` → controls append-before/after-transform behavior

This gives true mix-and-match modularity.

---

## 2.3 Config-first runtime
You want all of this configurable:

- db path
- source definitions
- per-folder behavior
- table definitions
- column mappings
- schema mapping
- transformation rules
- semantic sentence formation
- batch execution behavior

**Design decision:** create a **configuration model hierarchy in Pydantic**, loaded from YAML/JSON/TOML, with the UI acting as a config editor.

---

## 2.4 Analytical tables as first-class entities
You want tables like `portfolio_analysis` that depend on:

- investment purchases
- sales
- market data
- benchmark master
- benchmark data

and then compute:

- XIRR
- CAGR
- return metrics
- benchmark comparison
- exposure metrics
- summary analytics

**Design decision:** support **derived tables / analytical tables** as DAG nodes depending on base tables.

So the system has:

- **base ingestion tables**
- **canonical normalized tables**
- **derived analytical tables**
- **semantic document tables**
- **search/index tables**

---

## 2.5 Semantic narrative templates in config
You want to control the sentence formation from config/UI.

**Design decision:** each table can define:

- semantic title template
- semantic body template
- chunking behavior
- searchable keyword fields
- embedding inclusion rules

So semantic indexing becomes configurable, not hardcoded.

---

## 2.6 Dynamic tables
You want every config to define its own set of tables and columns.

This is the biggest architectural shift.

**Design decision:** use a **hybrid schema model**:

### Fixed engine tables
These are built-in and always exist:

- `etl_runs`
- `source_files`
- `lineage_events`
- `dead_letter_queue`
- `schema_registry`
- `semantic_documents`
- `semantic_embeddings`
- `config_snapshots`

### Dynamic user tables
These are created at runtime from config and compiled into:

- Pydantic models
- SQLite DDL
- validation rules
- lineage mappings
- semantic templates

This preserves your rule:

> Use Pydantic as the single source of truth.

Because the Pydantic models can be **generated dynamically at runtime** from configuration.

---

## 2.7 Phased implementation for AI agents
You want a handoff-ready roadmap so any AI agent can build this properly.

**Design decision:** define clear phases with:

- scope
- artifacts
- core classes
- tests
- acceptance criteria
- dependencies

I provide that in Section 15.

---

# 3. Architecture

## 3.1 Architectural style

Use **layered architecture with dependency inversion**, but make the runtime **config-driven**.

```text
UI / CLI Layer
    ↓
Application Services / ETL Orchestration
    ↓
Domain Models + Contracts
    ↓
Infrastructure Implementations

Cross-cutting:
Config, Logging, Registry, Lineage, Run Tracking, Schema Compilation
```

---

## 3.2 Required top-level layers

```text
config
domain
contracts
infrastructure
etl
tables
semantic
ui
```

---

## 3.3 Layer responsibilities

| Layer | Responsibility |
|---|---|
| `config` | load/validate project configuration, source configs, table configs, transformation configs |
| `domain` | core Pydantic models, enums, metadata definitions, runtime table schemas |
| `contracts` | abstract interfaces / protocols for readers, discoverers, selectors, loaders, semantic builders |
| `infrastructure` | SQLite access, local file scanning, Excel parsing, SQL connectors, hashing, plugin loading |
| `etl` | orchestration, run tracking, idempotency, validation, DLQ, lineage, schema sync |
| `tables` | generic configured pipeline + optional specialized custom pipelines |
| `semantic` | narrative generation, chunking, FTS5, sqlite-vec, embeddings, hybrid search |
| `ui` | CustomTkinter configuration editor and ETL runner |

---

## 3.4 Important refinement to your original idea

You earlier said:

> Each table should have its own class-based pipeline.

That is good for strongly modeled systems, but your later requirement says:

> tables must be dynamic and the app should only be an ETL engine.

To satisfy both, I recommend:

### Default
Use a **generic `ConfiguredTablePipeline`** that runs from config.

### Optional override
Allow a table to specify a **custom Python plugin class** when needed.

So the system supports both:

- **fully dynamic no-code tables**
- **specialized code-backed tables for edge cases**

This is the correct compromise.

---

# 4. Runtime Processing Model

## 4.1 Core execution graph

The runtime should process a configuration into a DAG like this:

```text
ProjectConfig
  ├── SourceDefinitions
  ├── TableDefinitions
  ├── DerivedTableDefinitions
  ├── SemanticDefinitions
  └── RuntimeSettings

Sources
  ↓
Raw extracted datasets
  ↓
Base / canonical tables
  ↓
Derived / analytical tables
  ↓
Semantic documents
  ↓
FTS5 + sqlite-vec indexes
```

---

## 4.2 Table types

Every table config should declare a `table_kind`:

- `base`
- `canonical`
- `derived`
- `semantic_projection`
- `system`

### Meaning
- **base**: lightly standardized ingestion table
- **canonical**: cleaned finance-ready table
- **derived**: computed from other tables
- **semantic_projection**: narrative/index materialization
- **system**: ETL metadata tables

---

# 5. Recommended Package Structure

```text
semantic_finance_etl/
├── config/
│   ├── models/
│   │   ├── project_config.py
│   │   ├── source_config.py
│   │   ├── table_config.py
│   │   ├── transform_config.py
│   │   ├── semantic_config.py
│   │   └── runtime_config.py
│   ├── loaders/
│   │   ├── yaml_loader.py
│   │   ├── json_loader.py
│   │   └── merged_config_loader.py
│   └── services/
│       ├── config_resolver.py
│       ├── config_merger.py
│       └── config_snapshot_service.py
│
├── domain/
│   ├── enums/
│   ├── models/
│   │   ├── base_model.py
│   │   ├── system_tables.py
│   │   ├── runtime_table_definition.py
│   │   ├── lineage_models.py
│   │   └── semantic_models.py
│   ├── schema/
│   │   ├── dynamic_model_factory.py
│   │   ├── sqlite_type_mapper.py
│   │   ├── schema_compiler.py
│   │   └── schema_diff.py
│   └── metadata/
│       ├── table_metadata.py
│       └── field_metadata.py
│
├── contracts/
│   ├── source_discoverer.py
│   ├── source_selector.py
│   ├── source_grouper.py
│   ├── source_reader.py
│   ├── transform_step.py
│   ├── validator.py
│   ├── loader.py
│   ├── repository.py
│   ├── semantic_builder.py
│   ├── embedding_provider.py
│   └── plugin_registry.py
│
├── infrastructure/
│   ├── discovery/
│   │   ├── filesystem_discoverer.py
│   │   └── sql_backup_discoverer.py
│   ├── selection/
│   │   ├── all_files_selector.py
│   │   ├── latest_modified_selector.py
│   │   ├── latest_created_selector.py
│   │   └── pattern_selector.py
│   ├── grouping/
│   │   ├── single_group_grouper.py
│   │   ├── folder_group_grouper.py
│   │   └── pattern_group_grouper.py
│   ├── readers/
│   │   ├── csv_reader.py
│   │   ├── excel_reader.py
│   │   ├── parquet_reader.py
│   │   ├── json_reader.py
│   │   ├── sqlite_reader.py
│   │   ├── sql_query_reader.py
│   │   └── duckdb_reader.py
│   ├── database/
│   │   ├── sqlite_connection.py
│   │   ├── sqlite_repository.py
│   │   ├── sqlite_upsert.py
│   │   ├── sqlite_schema_manager.py
│   │   └── sqlite_vec_manager.py
│   ├── parsing/
│   │   ├── messy_excel_parser.py
│   │   └── spatial_excel_locator.py
│   ├── hashing/
│   │   ├── file_hasher.py
│   │   ├── row_hasher.py
│   │   └── batch_hasher.py
│   ├── plugins/
│   │   ├── local_plugin_registry.py
│   │   └── plugin_loader.py
│   └── logging/
│       └── logging_config.py
│
├── etl/
│   ├── orchestration/
│   │   ├── run_etl_service.py
│   │   ├── pipeline_executor.py
│   │   ├── dag_builder.py
│   │   └── dependency_resolver.py
│   ├── runtime/
│   │   ├── pipeline_context.py
│   │   ├── execution_context.py
│   │   └── run_summary.py
│   ├── validation/
│   │   ├── pydantic_validator.py
│   │   └── validation_error_mapper.py
│   ├── loading/
│   │   ├── load_service.py
│   │   └── upsert_planner.py
│   ├── lineage/
│   │   ├── lineage_recorder.py
│   │   └── source_to_row_mapper.py
│   ├── dlq/
│   │   ├── dlq_service.py
│   │   └── dlq_record_builder.py
│   └── tracking/
│       ├── run_tracker.py
│       ├── source_file_tracker.py
│       └── idempotency_service.py
│
├── tables/
│   ├── configured_table_pipeline.py
│   ├── derived_table_pipeline.py
│   ├── transform_engine.py
│   ├── step_factory.py
│   └── custom/
│       └── __init__.py
│
├── semantic/
│   ├── narrative/
│   │   ├── template_renderer.py
│   │   ├── sentence_builder.py
│   │   └── semantic_projection_service.py
│   ├── embeddings/
│   │   ├── sentence_transformer_provider.py
│   │   ├── embedding_cache.py
│   │   └── embedding_service.py
│   ├── indexing/
│   │   ├── fts5_indexer.py
│   │   ├── vector_indexer.py
│   │   └── hybrid_search_service.py
│   └── chunking/
│       └── chunk_strategy.py
│
├── ui/
│   ├── app.py
│   ├── controllers/
│   ├── viewmodels/
│   ├── views/
│   └── services/
│
└── tests/
    ├── unit/
    ├── integration/
    ├── contract/
    └── fixtures/
```

---

# 6. Core Abstractions

## 6.1 Plugin architecture

The plugin model should be explicit and stable.

## Plugin categories
1. `SourceDiscoverer`
2. `SourceSelector`
3. `SourceGrouper`
4. `SourceReader`
5. `TransformStep`
6. `Validator`
7. `Loader`
8. `SemanticBuilder`
9. `EmbeddingProvider`
10. `CustomPipeline`

---

## 6.2 Key interfaces and purpose

| Interface | Purpose |
|---|---|
| `SourceDiscoverer` | find eligible source assets from local file system / DB location |
| `SourceSelector` | choose latest/all/matching/nth set |
| `SourceGrouper` | combine selected sources into logical groups |
| `SourceReader` | read selected source into DataFrame/LazyFrame |
| `TransformStep` | apply one transformation operation |
| `Validator` | validate rows using runtime-generated Pydantic model |
| `Loader` | UPSERT into SQLite |
| `SemanticBuilder` | generate configurable narrative text from row(s) |
| `EmbeddingProvider` | create local embeddings |
| `CustomPipeline` | escape hatch for bespoke logic |

---

## 6.3 Recommended pipeline context objects

These runtime objects will reduce coupling:

- `ProjectContext`
- `ExecutionContext`
- `PipelineContext`
- `SourceGroup`
- `TableExecutionPlan`
- `LineageContext`

This avoids passing random dictionaries everywhere.

---

# 7. Configuration-Driven Architecture

## 7.1 Recommended config layout

Use modular YAML files:

```text
configs/
├── project.yaml
├── runtime.yaml
├── sources/
│   ├── bank_exports.yaml
│   ├── broker_backups.yaml
│   └── market_data.yaml
├── tables/
│   ├── transactions.yaml
│   ├── investments.yaml
│   └── portfolio_analysis.yaml
└── semantics/
    ├── transactions_semantic.yaml
    └── portfolio_analysis_semantic.yaml
```

This is better than one massive config file.

---

## 7.2 Top-level config concepts

Every project config should include:

- project metadata
- SQLite db path
- plugin registry paths
- source definitions
- table definitions
- semantic settings
- execution settings
- idempotency settings
- indexing settings

---

## 7.3 Example: folder of SQLite backups, choose latest modified, run query

```yaml
sources:
  - source_id: broker_sqlite_backups
    discoverer: filesystem
    selector: latest_modified
    grouper: single_group
    path: ./data/raw/broker_backups
    recursive: true
    include_patterns: ["*.sqlite", "*.db"]
    reader:
      type: sqlite_query
      sql: |
        SELECT
          trade_date,
          symbol,
          transaction_type,
          quantity,
          price,
          amount,
          account_name
        FROM trades
    output_mode: single_dataset
    target_tables: ["investment_transactions"]
```

This exactly supports the use case you described.

---

## 7.4 Example: same folder, load all SQLite DBs and union results

```yaml
sources:
  - source_id: all_broker_backups
    discoverer: filesystem
    selector: all_files
    grouper: single_group
    path: ./data/raw/broker_backups
    recursive: true
    include_patterns: ["*.sqlite", "*.db"]
    reader:
      type: sqlite_query
      sql: "SELECT * FROM trades"
    combine_strategy: transform_then_append
    target_tables: ["investment_transactions"]
```

---

## 7.5 Example: dynamic table definition

```yaml
tables:
  - table_name: investment_transactions
    table_kind: canonical
    primary_key_strategy:
      type: deterministic_hash
      fields:
        - account_name
        - symbol
        - trade_date
        - transaction_type
        - quantity
        - amount
    columns:
      - name: canonical_id
        type: str
        nullable: false
      - name: trade_date
        type: date
      - name: symbol
        type: str
      - name: transaction_type
        type: str
      - name: quantity
        type: decimal
      - name: price
        type: decimal
      - name: amount
        type: decimal
      - name: account_name
        type: str
    load:
      mode: upsert
      record_hash: true
```

---

# 8. Dynamic Tables and Runtime Pydantic Models

## 8.1 How to satisfy “Pydantic is the schema source of truth” with dynamic tables

Use this pattern:

```text
Config → RuntimeTableDefinition → Runtime Pydantic Model → SQLite DDL
```

So Pydantic is still the truth, but it is **generated from config**.

---

## 8.2 Recommended model strategy

### Built-in static Pydantic models
Use normal code-defined models for:

- ETL system metadata tables
- lineage tables
- DLQ tables
- semantic index metadata tables

### Runtime-generated Pydantic models
Use `pydantic.create_model()` for:

- user-defined finance tables
- custom analytical tables
- per-project schemas

---

## 8.3 Schema evolution rules

### Safe automatic changes
- add nullable column
- add non-null column with default
- widen text-like fields
- add semantic metadata field

### Controlled/manual changes
- change data type incompatibly
- remove column
- rename column
- split table
- change primary key logic

For controlled changes, create a schema diff and require confirmation or migration plan.

---

# 9. Source Discovery, Selection, Grouping, and Reading

This is one of the most important parts of your design.

## 9.1 Why these must be separate
Because these are different decisions:

- **what exists?** → discovery
- **which ones to use?** → selection
- **how to bundle them?** → grouping
- **how to read them?** → reader
- **when to combine?** → combine strategy

If you combine these into one class, extensibility dies.

---

## 9.2 Supported selector plugins

At minimum:

- `all_files`
- `latest_modified`
- `latest_created`
- `oldest_modified`
- `top_n_latest`
- `date_range`
- `filename_regex`
- `manual_list`
- `unprocessed_only`
- `changed_since_last_run`

---

## 9.3 Supported grouping plugins

- `single_group`
- `group_by_parent_folder`
- `group_by_filename_pattern`
- `group_by_date_partition`
- `group_by_source_type`

---

## 9.4 Supported reader plugins

- `csv_reader`
- `excel_reader`
- `parquet_reader`
- `json_reader`
- `sqlite_table_reader`
- `sqlite_query_reader`
- `sql_query_reader`
- `duckdb_reader`

For “other SQL sources,” the abstraction should support either:

- table read
- custom SQL query
- incremental SQL query with parameter injection

---

## 9.5 Combine strategies

| Strategy | Meaning | Best use case |
|---|---|---|
| `single_file` | process one selected file only | latest report |
| `raw_then_transform` | union raw data, then transform once | homogeneous files |
| `transform_then_append` | clean each file first, then union canonical rows | messy files |
| `query_each_then_union` | execute same SQL on many DB files, then union | folder of SQLite backups |
| `partitioned_batches` | process by time/account/other partition | large datasets |

### My recommendation
- default to `transform_then_append` for messy finance inputs
- use `raw_then_transform` only when schemas are truly stable
- use `query_each_then_union` for many SQLite backup files

---

# 10. Transformation Engine

## 10.1 Design principle
Transformations should be **declarative where possible**, with a **plugin escape hatch**.

So the engine should support:

1. **config-defined standard transformations**
2. **custom Python transform plugins** for complex edge cases

---

## 10.2 Transformation step library

Support these operations as first-class config steps:

- `select`
- `rename`
- `cast`
- `drop`
- `filter`
- `sort`
- `deduplicate`
- `fill_null`
- `replace`
- `derive_column`
- `explode`
- `pivot`
- `unpivot`
- `join`
- `group_by_agg`
- `window`
- `rolling`
- `cumulative`
- `union`
- `lookup`
- `asof_join`
- `rank`
- `normalize_text`
- `parse_date`
- `parse_decimal`
- `map_values`
- `custom_plugin`

This is enough power for 90% of finance workflows.

---

## 10.3 Why Polars LazyFrame is the right backbone
Because you want:

- speed
- composability
- lazy optimization
- batch-friendly transformations
- SQL-like analytical operations

Use pandas only for messy Excel edge cases or when spatial parsing is required.

---

## 10.4 How analytical table generation should work

A derived table config should declare:

- dependencies
- transformation steps
- load mode
- refresh behavior
- semantic behavior

Example:

```yaml
tables:
  - table_name: portfolio_analysis
    table_kind: derived
    depends_on:
      - investment_transactions
      - market_prices
      - benchmark_master
      - benchmark_prices
    build:
      engine: polars
      steps:
        - type: join
          left: investment_transactions
          right: market_prices
          on: [symbol]
          how: left
        - type: derive_column
          name: market_value
          expression: "quantity_held * close_price"
        - type: group_by_agg
          by: [portfolio_id, valuation_date]
          metrics:
            - name: total_market_value
              expression: "sum(market_value)"
        - type: window
          partition_by: [portfolio_id]
          order_by: [valuation_date]
          expressions:
            - name: running_cost
              expression: "sum(cost_basis)"
        - type: custom_plugin
          plugin: semantic_finance_etl.tables.custom.xirr_step.XirrStep
```

---

## 10.5 SQL generation explanation using two important SQL operations

Because you asked for AI-agent-ready clarity, here is how config-driven transforms should conceptually compile.

### Example 1: `join`
Config:

```yaml
- type: join
  left: investment_transactions
  right: market_prices
  on: [symbol, valuation_date]
  how: left
```

Conceptual SQL equivalent:

```sql
SELECT
    t.*,
    p.close_price
FROM investment_transactions t
LEFT JOIN market_prices p
    ON t.symbol = p.symbol
   AND t.valuation_date = p.valuation_date;
```

### Example 2: `group_by_agg`
Config:

```yaml
- type: group_by_agg
  by: [portfolio_id]
  metrics:
    - name: total_cost
      expression: "sum(cost_basis)"
    - name: total_value
      expression: "sum(market_value)"
```

Conceptual SQL equivalent:

```sql
SELECT
    portfolio_id,
    SUM(cost_basis) AS total_cost,
    SUM(market_value) AS total_value
FROM portfolio_positions
GROUP BY portfolio_id;
```

### Example 3: `window`
Config:

```yaml
- type: window
  partition_by: [portfolio_id]
  order_by: [valuation_date]
  expressions:
    - name: running_value
      expression: "sum(market_value)"
```

Conceptual SQL equivalent:

```sql
SELECT
    portfolio_id,
    valuation_date,
    market_value,
    SUM(market_value) OVER (
        PARTITION BY portfolio_id
        ORDER BY valuation_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_value
FROM portfolio_daily_values;
```

So your transformation DSL should feel like a structured abstraction over:

- `JOIN`
- `GROUP BY`
- `WINDOW FUNCTIONS`
- expression columns
- unions and filters

This will make it powerful enough for serious analytical finance tables.

---

# 11. Analytical Tables as First-Class DAG Nodes

## 11.1 Table dependency graph
You explicitly want tables built from other tables. Therefore every table config may optionally declare:

- `depends_on`
- `refresh_policy`
- `materialization`
- `rebuild_on_dependency_change`

---

## 11.2 Materialization modes
Support:

- `table`
- `view`
- `incremental_table`
- `ephemeral` (in-memory for intermediate steps)

### Recommendation
- use `table` for Power BI consumption
- use `view` for lightweight reusable projections
- use `incremental_table` carefully after base engine stabilizes

---

## 11.3 Examples of derived finance tables
- `portfolio_analysis`
- `daily_holdings`
- `realized_gains`
- `unrealized_gains`
- `cashflow_series`
- `benchmark_comparison`
- `goal_progress`
- `asset_allocation_snapshot`
- `tax_lot_summary`

---

# 12. Semantic Layer

## 12.1 Semantic pipeline
For each table, optionally generate a semantic projection:

```text
table rows
  → semantic sentence / narrative template
  → chunking
  → FTS5 document
  → embedding vector
  → hybrid search index
```

---

## 12.2 Configurable semantic templates
Each table should support config like:

```yaml
semantics:
  - table_name: investment_transactions
    enabled: true
    title_template: "Investment transaction for {{ account_name }}"
    body_template: >
      On {{ trade_date }}, {{ account_name }} {{ transaction_type }}
      {{ quantity }} units of {{ symbol }} for {{ amount }}.
    tags:
      - "{{ symbol }}"
      - "{{ transaction_type }}"
      - "{{ account_name }}"
```

This lets you edit wording from the UI.

---

## 12.3 Semantic configuration options
Per table:

- enabled/disabled
- template version
- title template
- body template
- tags template
- chunk strategy
- include/exclude columns
- row-level vs grouped semantic docs
- re-embed on template change
- search ranking weights

---

## 12.4 Search design
Use hybrid search:

1. **FTS5** for keyword and exact-ish lookup
2. **sqlite-vec** for semantic similarity
3. merge/rerank both locally

This gives:

- precise search
- semantic retrieval
- good future support for local AI agents

---

# 13. SQLite Database Design

## 13.1 Database zones

Use logical zones in one SQLite DB:

### A. System zone
- `etl_runs`
- `source_files`
- `source_groups`
- `lineage_events`
- `dead_letter_queue`
- `schema_registry`
- `config_snapshots`

### B. Data zone
- dynamic finance tables
- canonical tables
- derived analytical tables

### C. Semantic zone
- `semantic_documents`
- `semantic_chunks`
- `semantic_embeddings`
- FTS5 virtual tables
- sqlite-vec tables

---

## 13.2 Pydantic-driven schema creation
Never treat `schema.sql` as the source of truth.

Instead:

```text
Config → Pydantic model → SQLite DDL generator → DB sync
```

Generated SQL is fine. Handwritten static schema is not the master.

---

# 14. Idempotency, Run Tracking, DLQ, and Lineage

## 14.1 Idempotency layers
You already want this, and it remains essential.

### File-level
Track:

- file path
- file size
- modified timestamp
- created timestamp if available
- content hash

### Group-level
Track source group hash so batches can be skipped or re-run intelligently.

### Row-level
Track:

- `canonical_id`
- `record_hash`

### Load-level
Use SQLite UPSERT behavior:

- insert if new
- update if changed
- skip if identical

---

## 14.2 Dead letter queue
Every failed row should persist with:

- run id
- source id
- file path
- row number
- raw payload
- validation errors
- transformation step
- timestamp

This is non-negotiable for a serious ETL engine.

---

## 14.3 Lineage
At minimum you should be able to answer:

- which file produced this row?
- which run loaded it?
- which config version was used?
- which transformation steps touched it?
- which semantic document came from it?

This is critical for trust and debugging.

---

# 15. UI Architecture

## 15.1 Principle
The UI must **never contain business logic**.

It should only:

- edit config
- validate config
- preview discovered files
- preview transformations
- run ETL
- show run status
- display DLQ issues
- trigger semantic rebuild

Business logic remains in application services.

---

## 15.2 Recommended UI modules
- Project selector
- Source config editor
- Table schema editor
- Transformation pipeline editor
- Semantic template editor
- Execution dashboard
- Run history
- DLQ browser
- Search tester

---

## 15.3 Key UI workflows
1. create/update config
2. test source discovery
3. preview extraction
4. preview transformation
5. save config snapshot
6. run ETL batch
7. inspect results/errors
8. rebuild semantic indexes

---

# 16. Phase-by-Phase Implementation Plan

This is the handoff section for future AI agents.

## Phase 1 — Project skeleton and config foundation
### Goal
Establish the package structure and config models.

### Deliverables
- package skeleton
- Pydantic config models
- config loader
- config merger
- project bootstrap

### Acceptance criteria
- load `project.yaml`
- validate source/table definitions
- print runtime plan successfully

---

## Phase 2 — Plugin registry and discovery framework
### Goal
Implement pluggable discovery/selection/grouping.

### Deliverables
- `SourceDiscoverer` interface
- `SourceSelector` interface
- `SourceGrouper` interface
- local plugin registry
- filesystem discoverer
- latest/all selectors

### Acceptance criteria
- folder scan works
- latest modified file can be selected
- all files can be selected
- grouping output is deterministic

---

## Phase 3 — Source readers
### Goal
Support core source types.

### Deliverables
- CSV reader
- Excel reader
- Parquet reader
- JSON reader
- SQLite query reader
- generic SQL query reader abstraction

### Acceptance criteria
- each reader returns standardized frame contract
- folder of SQLite files can be queried through config
- messy Excel fallback path is defined

---

## Phase 4 — Runtime schema system
### Goal
Generate runtime Pydantic models and SQLite tables from config.

### Deliverables
- runtime table definition models
- dynamic Pydantic model factory
- SQLite schema compiler
- schema diff engine

### Acceptance criteria
- new dynamic table config creates SQLite table
- added column updates schema safely
- schema registry is tracked

---

## Phase 5 — ETL orchestration core
### Goal
Build the generic configured pipeline.

### Deliverables
- run tracker
- pipeline executor
- configured table pipeline
- execution context
- source file tracking
- idempotency service

### Acceptance criteria
- one config can execute end to end
- rerun skips unchanged files
- changed files reload correctly

---

## Phase 6 — Transformation engine
### Goal
Support config-defined transformation steps.

### Deliverables
- transform step contracts
- step factory
- Polars-backed transform engine
- standard steps library

### Acceptance criteria
- select/rename/cast/filter/join/group/window work
- step chaining works
- validation-ready output is produced

---

## Phase 7 — Validation, load, and DLQ
### Goal
Make ingestion trustworthy.

### Deliverables
- Pydantic validator
- row error mapping
- DLQ persistence
- SQLite UPSERT load service
- record hash strategy

### Acceptance criteria
- invalid rows go to DLQ
- valid rows load cleanly
- identical rows do not duplicate
- changed rows update correctly

---

## Phase 8 — Derived/analytical tables
### Goal
Support table dependencies and analytical materializations.

### Deliverables
- DAG builder
- dependency resolver
- derived table pipeline
- materialization modes
- XIRR/CAGR custom plugin hooks

### Acceptance criteria
- derived tables can depend on base tables
- join/group/window logic works across tables
- portfolio analysis can be materialized

---

## Phase 9 — Semantic layer
### Goal
Enable local search and future AI use.

### Deliverables
- template renderer
- semantic document builder
- FTS5 indexer
- sentence-transformers provider
- sqlite-vec indexing
- hybrid search service

### Acceptance criteria
- table rows become semantic docs
- semantic template changes trigger rebuild
- keyword + semantic retrieval both work

---

## Phase 10 — UI
### Goal
Build the local desktop control center.

### Deliverables
- CustomTkinter shell
- config editor screens
- run execution dashboard
- DLQ viewer
- semantic preview panel

### Acceptance criteria
- config can be edited and saved
- ETL can be triggered from UI
- run history and errors are visible

---

## Phase 11 — Hardening
### Goal
Make it production-style.

### Deliverables
- structured logging
- integration tests
- contract tests for plugins
- fixture datasets
- performance profiling
- docs

### Acceptance criteria
- stable reruns
- test coverage on critical flows
- plugin contract guarantees
- Power BI-ready tables verified

---

# 17. What AI Agents Should Build First

If you want agents to “knock it out of the park,” the build order should be:

1. config models
2. plugin registry
3. discovery/selection/grouping
4. readers
5. dynamic schema compiler
6. generic configured pipeline
7. transform engine
8. validation + DLQ + UPSERT
9. derived tables
10. semantic indexing
11. UI

Do **not** start with the UI.
Do **not** start with embeddings.
Do **not** hardcode finance tables too early.

Foundation first.

---

# 18. Final Architecture Decision

## The correct final shape is:

### Engine
A **generic local ETL runtime**

### Behavior
**Config-driven**, **plugin-based**, **idempotent**, **schema-aware**, **semantically enabled**

### Data model
Combination of:

- fixed system tables
- dynamic runtime-generated user tables
- derived analytical tables
- semantic projection/index tables

### Processing style
- local only
- Polars-first
- SQLite target
- Pydantic-driven validation/schema
- FTS5 + sqlite-vec for retrieval

### Extension strategy
- add new source types via readers
- add new discovery logic via discoverer/selector plugins
- add new transforms via transform-step plugins
- add new table behavior via config or custom pipeline plugin
- add new semantic styles via template config

---

# 19. My Strong Recommendations

## Do this
- build a **generic `ConfiguredTablePipeline`**
- keep source discovery separate from source reading
- generate Pydantic models dynamically from config
- make derived tables first-class DAG nodes
- store semantic templates in config
- version config snapshots per run
- treat lineage as a core feature, not a nice-to-have

## Do not do this
- do not hardcode all tables in Python classes
- do not mix UI with ETL logic
- do not make static SQL schema the master
- do not make one giant “reader” class
- do not skip DLQ and lineage early

---

# 20. Best Next Step

The next practical step is **not code for readers yet**.

The next correct step is:

## Step 1
Define the **configuration model hierarchy**.

Specifically:

- `ProjectConfig`
- `SourceConfig`
- `ReaderConfig`
- `SelectorConfig`
- `TableConfig`
- `ColumnConfig`
- `TransformStepConfig`
- `SemanticTemplateConfig`
- `RuntimeSettings`

Once that exists, the rest of the engine can be built cleanly.

If you want, I can now take this design and move to the next step exactly as you requested:

## Next deliverable
**Package structure + core abstractions, then first file implementation**

I would start with:

`semantic_finance_etl/config/models/project_config.py`

and I’ll generate it **one file at a time**, complete and runnable.