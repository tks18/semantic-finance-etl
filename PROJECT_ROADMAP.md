I reviewed your current design doc and your new requirements change the architecture in an important way:

> **This should not be a hardcoded finance ETL app with a few table classes.**
>
> It should be a **local ETL engine** that can run finance-oriented, config-defined, plugin-extended data workflows.

That is the right direction.

Below is a **reframed, expanded, v2 design document** for `semantic-finance-ETL` that incorporates your five changes and aligns them with your original rules: local-first, Pydantic-driven, SQLite target, Polars-heavy, plugin-based, idempotent, semantic-ready.

# `semantic-finance-ETL` v2 Design Document

## 1. Executive Summary

`semantic-finance-ETL` will be a **local-first, privacy-preserving, configuration-driven ETL engine** for personal finance and investment data.

It will:

- ingest data from **Excel, CSV, parquet, JSON, SQLite, and other local SQL sources**
- discover source inputs using **pluggable discovery strategies**
- transform data using **configurable pipelines plus optional custom plugins**
- validate rows using **Pydantic-generated runtime models**
- load data into a **semantically rich local SQLite database**
- build **derived analytical tables** from base tables
- maintain **lineage, idempotency, and dead-letter handling**
- support **FTS5 + sqlite-vec** for future local semantic and agentic usage
- expose everything via **configuration**, with a future **CustomTkinter UI** as the configuration and orchestration surface

## 2. The Most Important Architectural Shift

Your original doc assumed a partially hardcoded set of finance tables like `transactions`, `accounts`, `market_price`, etc.

Your new requirement changes that.

## Final architectural stance

The system should have **three layers of meaning**:

### A. ETL Engine Layer
Pure engine capabilities:

- config loading
- source discovery
- source reading
- transformation execution
- validation
- loading
- run tracking
- DLQ
- lineage
- schema compilation
- semantic indexing

This layer should **not hardcode business tables**.

### B. Domain Pack Layer
Optional reusable finance definitions:

- starter schemas for `transactions`
- starter schemas for `investment_transactions`
- starter derived tables like `portfolio_analysis`
- reusable transformation plugins
- reusable semantic narrative builders

This is optional convenience, not core engine truth.

### C. Project Configuration Layer
The real application definition:

- what sources exist
- how they are discovered
- what tables to create
- which columns to map
- what types to use
- what transformations to run
- what derived tables depend on which base tables
- what semantic tables to index

This is where the actual behavior lives.

> **Therefore: the app is an ETL engine; each project config defines its own finance warehouse.**

That directly satisfies your requirement that the app itself should not hardcode tables.

---

# 3. Core Design Principles

## 3.1 Local-first only

Everything runs locally:

- source files from local disk
- source databases from local files or local network-accessible DBs
- local SQLite warehouse
- local embeddings
- local FTS5
- local sqlite-vec
- no cloud services
- no hosted vector DB
- no external APIs

## 3.2 Configuration is the primary business definition

The configuration should define:

- database path
- sources
- discoverers
- file patterns
- connection strings for local SQL sources
- append strategy
- table definitions
- column mappings
- transformations
- validation rules
- load mode
- derived table dependencies
- semantic indexing behavior

## 3.3 Pydantic remains the schema source of truth

You explicitly want Pydantic as the single source of truth.

That still works even with dynamic tables.

We solve the tension this way:

### Static Pydantic models
Used for system tables:

- ETL runs
- source assets
- pipeline results
- dead letter queue
- semantic documents
- embeddings
- lineage records

### Runtime-generated Pydantic models
Used for config-defined business tables:

- `transactions`
- `investment_transactions`
- `portfolio_analysis`
- any custom user table

These models are generated from config at runtime using validated table metadata.

So there is still **no separate `schema.sql` truth**.

## 3.4 Metadata-driven, plugin-extended

Most workflows should work through config.

But when config is not enough, the engine should support plugin hooks for:

- discovery
- reading
- transformation
- validation enrichment
- key generation
- derived table calculation
- narrative generation
- semantic chunking

## 3.5 Idempotent by design

The engine must safely re-run without duplicating data.

It should combine:

- source fingerprinting
- run tracking
- deterministic keys
- row hashes
- UPSERT rules
- DLQ deduplication
- derived table refresh policies

---

# 4. Scope of Supported Source Types

The system should support these local source families.

## 4.1 File-based sources

- `.xlsx`
- `.xls`
- `.csv`
- `.tsv`
- `.parquet`
- `.json`
- newline-delimited JSON
- local text extracts when needed

## 4.2 Local database sources

- SQLite
- DuckDB
- PostgreSQL running locally
- MySQL running locally
- SQL Server running locally
- any local SQL source supported by a plugin/driver

## 4.3 Source object abstraction

The old concept of `SourceFile` is too narrow now.

Because not all sources are files.

So the generalized concept should be:

## `SourceAsset`

A `SourceAsset` is one discoverable or executable input unit.

Examples:

- a file on disk
- a table in SQLite
- a SQL query result
- a view in a local database
- a folder snapshot

Suggested types:

- `FILE`
- `SQLITE_TABLE`
- `SQL_TABLE`
- `SQL_QUERY`
- `PARQUET_FILE`
- `JSON_FILE`
- `CSV_FILE`
- `EXCEL_FILE`

This is a better long-term abstraction than `SourceFile`.

---

# 5. Source Discovery Plugin Architecture

This is one of your most important additions.

You do **not** want a single hardcoded folder-scanning behavior.

You want source selection to be configurable.

That means discovery becomes a first-class subsystem.

## 5.1 Source discovery responsibilities

A discoverer should answer:

- what source assets are eligible for this run?
- which file(s) from a folder should be picked?
- should we recurse?
- should we choose latest modified, latest created, all files, only new files, matching partitions, or a manifest-defined subset?

## 5.2 Discoverer plugin types

Recommended built-in discoverers:

### File discoverers
- `AllFilesDiscoverer`
- `LatestModifiedFileDiscoverer`
- `LatestCreatedFileDiscoverer`
- `NewestNFilesDiscoverer`
- `PatternMatchedFileDiscoverer`
- `RecursiveFolderDiscoverer`
- `UnprocessedFilesDiscoverer`
- `ModifiedSinceWatermarkDiscoverer`
- `ManifestListDiscoverer`

### SQL discoverers
- `SqlTableDiscoverer`
- `SqlQueryDiscoverer`
- `SqlIncrementalWindowDiscoverer`

### Composite discoverers
- `UnionDiscoverer`
- `PriorityDiscoverer`
- `FirstMatchDiscoverer`

## 5.3 Discovery strategies you explicitly need

From your requirement, these must exist:

- take only latest modified file
- take only latest created file
- take all files in folder
- recursive ingestion
- file grouping before transform
- transform before append
- append before transform

## 5.4 Discovery output

Every discoverer should return standardized `DiscoveredAsset` metadata:

- `asset_id`
- `source_name`
- `asset_type`
- `location`
- `relative_path`
- `extension`
- `size_bytes`
- `created_at`
- `modified_at`
- `fingerprint_candidate`
- `partition_values`
- `group_key`
- `metadata_json`

---

# 6. Append and Processing Strategy Model

You called out a very important need: sometimes data must be combined before transform, sometimes after.

This should be explicit in config.

## 6.1 Processing strategy enum

Recommended:

- `SINGLE_ASSET`
- `RAW_THEN_TRANSFORM`
- `TRANSFORM_THEN_APPEND`
- `APPEND_CANONICAL_THEN_LOAD`
- `SNAPSHOT_REPLACE`
- `INCREMENTAL_UPSERT`

## 6.2 When to use which

### `RAW_THEN_TRANSFORM`
Use when files are structurally similar.

Example:
- monthly CSV exports with same columns

Flow:
1. discover all files
2. read them all
3. append raw frames
4. transform once
5. validate
6. load

### `TRANSFORM_THEN_APPEND`
Use when files are messy or inconsistent.

Example:
- old/new broker exports
- Excel sheets with different offsets
- files with different headers

Flow:
1. discover files
2. read one
3. clean one
4. transform one
5. validate one
6. append canonical rows
7. load

### `SINGLE_ASSET`
Use for one-off extracts or latest-file loads.

### `SNAPSHOT_REPLACE`
Use for holdings snapshot-style tables.

### `INCREMENTAL_UPSERT`
Use for transactions and market history.

---

# 7. Dynamic, Config-Defined Tables

This is the second biggest architectural change.

## Final position

Business tables should be defined in config, not in code.

The engine should not know in advance whether the project has:

- `transactions`
- `expenses`
- `credit_card_statement_lines`
- `investment_transactions`
- `portfolio_analysis`
- `benchmark_rollup`
- `crypto_positions`
- `insurance_premium_schedule`

It should compile these from config.

## 7.1 Table definition model

Each table config should define:

- table name
- kind: base / derived / semantic / staging
- description
- primary key strategy
- columns
- type definitions
- nullable rules
- unique constraints
- indexes
- source bindings
- mapping rules
- transformation pipeline
- validation rules
- load strategy
- semantic indexing flag

## 7.2 Column definition model

Each column config should define:

- column name
- source aliases
- logical type
- SQLite type
- nullable
- default
- description
- semantic label
- indexing hint
- whether included in natural key
- whether included in embedding text
- whether included in lineage/audit

## 7.3 Runtime model generation

At runtime:

1. config is loaded into Pydantic config models
2. table specs are compiled into runtime Pydantic row models
3. runtime models are compiled into SQLite DDL
4. same runtime models validate incoming rows
5. schema diff logic compares desired vs actual DB tables

That preserves your rule:

> **Pydantic remains the single source of truth.**

---

# 8. Reconciling “Dynamic Tables” with “One Pipeline per Table”

Your original architecture expects one pipeline class per table.

Your new requirement says tables are dynamic and should not be hardcoded.

These can be reconciled cleanly.

## Recommended model

### Generic pipeline engine
Use a generic class:

- `ConfiguredTablePipeline`

This pipeline reads a `TableSpec` and executes:

- extract
- transform
- validate
- load

### Optional specialized plugin pipeline
For complex tables, allow:

- `PythonTransformPlugin`
- `SqlDerivedTablePlugin`
- `PolarsDerivedTablePlugin`

So the system becomes:

- **config-driven by default**
- **plugin-driven when complexity demands**

That is the right compromise.

Do **not** create a custom Python class for every possible business table from day one.

Instead:

- generic pipeline for most tables
- specialized subclasses/plugins only where truly needed

---

# 9. Derived and Analytical Tables

This is a major requirement you added, and it should be a first-class feature.

You want tables like:

- `portfolio_analysis`
- `xirr_results`
- `cagr_results`
- `benchmark_comparison`
- `asset_allocation`
- `performance_rollups`

that depend on other tables such as:

- `investment_purchases`
- `investment_sales`
- `market_data`
- `benchmark_master`
- `benchmark_data`

## 9.1 Table kinds

We should formally distinguish:

- `BASE_TABLE`
- `DERIVED_TABLE`
- `MATERIALIZED_ANALYTICAL_TABLE`
- `VIEW`
- `SEMANTIC_DOCUMENT_TABLE`

## 9.2 Dependency graph

Every derived table should declare dependencies.

Example:

```yaml
depends_on:
  - investment_transactions
  - market_prices
  - benchmark_master
  - benchmark_prices
```

The engine should build a DAG and execute in dependency order.

## 9.3 Derived table execution engines

Support at least these:

- `SQL`
- `POLARS`
- `PYTHON_PLUGIN`

## 9.4 Materialization modes

Derived outputs should support:

- `table`
- `view`
- `incremental_table`
- `replace_table`

## 9.5 Example analytical pipeline

For `portfolio_analysis`:

1. load base transactional and market tables
2. compute cash flows
3. join benchmark metadata
4. compute current valuation
5. calculate XIRR, CAGR, drawdown, return attribution
6. materialize `portfolio_analysis`
7. create semantic narratives
8. embed and index for search

This satisfies your requirement that analytical outputs themselves must also feed the semantic layer.

---

# 10. Semantic Layer Design

The semantic layer should not only index raw transactions.

It should also index:

- portfolio summaries
- derived metrics
- benchmark comparisons
- anomaly findings
- validation errors
- lineage summaries
- user notes

## 10.1 Phased semantic architecture

### Phase 1: FTS5
- keyword search
- very fast
- zero extra model complexity

### Phase 2: semantic documents
Convert rows or groups of rows into natural-language text.

Example:
- “Portfolio Alpha returned 12.4% CAGR over 3 years and underperformed benchmark NIFTY 50 by 2.1%.”

### Phase 3: embeddings
Use local `sentence-transformers`:

- preferably `all-MiniLM-L6-v2`

### Phase 4: vector search
Store embeddings using `sqlite-vec`.

### Phase 5: hybrid search
Combine:

- FTS5 score
- vector similarity
- structured filters
- semantic table metadata

## 10.2 Semantic document pipeline

For each indexed table:

1. select rows or row groups
2. build narrative text using templates/plugins
3. chunk if needed
4. compute embedding
5. store in semantic documents table
6. update FTS5
7. update vector store

## 10.3 Important design decision

Do not embed every raw row blindly.

Use configurable indexing policies:

- embed per row
- embed per account-period
- embed per portfolio-period
- embed only derived tables
- embed only high-value tables

---

# 11. Schema Strategy

## 11.1 No static `schema.sql` as primary truth

Correct.

The database schema should be generated from:

- static Pydantic system models
- runtime-generated Pydantic business models from config

## 11.2 SQLite generation

The schema compiler should generate:

- `CREATE TABLE`
- indexes
- unique constraints
- FTS tables
- vec tables
- metadata catalog entries

## 11.3 Schema evolution

Because tables are dynamic, schema evolution is critical.

Recommended schema migration modes:

- additive column add
- index add/drop
- metadata-only update
- rebuild table for breaking changes
- versioned derived table regeneration

## 11.4 Schema catalog

Maintain system metadata tables such as:

- `meta_tables`
- `meta_columns`
- `meta_indexes`
- `meta_table_versions`
- `meta_config_versions`

This gives both Power BI and future agents a semantic catalog.

---

# 12. Idempotency and Lineage

This remains non-negotiable.

## 12.1 Source-level idempotency

For files, track:

- path
- size
- modified timestamp
- created timestamp
- content hash

For SQL sources, track:

- source name
- connection alias
- table/query name
- query text hash
- optional source watermark
- extract fingerprint

## 12.2 Row-level idempotency

Each loaded row should include:

- `canonical_id`
- `record_hash`
- `source_asset_id`
- `created_run_id`
- `updated_run_id`

## 12.3 Dead-letter idempotency

DLQ rows should also have deterministic hashes to avoid repeated duplicate invalid rows on reruns.

## 12.4 Derived table idempotency

Derived tables should store:

- dependency signature
- calculation version
- upstream run references
- refresh mode

That lets you know whether a derived table is stale or reproducible.

---

# 13. Configuration Architecture

This is the heart of the system.

## 13.1 Config file philosophy

A project should be runnable from configuration alone.

The UI should simply edit this configuration.

## 13.2 Config layers

Recommended config stack:

### A. `app.yaml`
Engine-wide settings:
- project name
- SQLite path
- logging
- semantic defaults
- plugin paths

### B. `sources/*.yaml`
Source definitions:
- file folders
- SQL connections
- discovery strategies
- reader settings

### C. `tables/*.yaml`
Table definitions:
- schema
- mappings
- transforms
- load rules

### D. `derived/*.yaml`
Derived table definitions:
- dependencies
- engine
- SQL or plugin reference
- materialization mode

### E. `semantic/*.yaml`
Semantic indexing rules:
- table selection
- narrative templates
- embedding settings

## 13.3 Workspace concept

Support multiple projects via workspaces:

```text
workspaces/
  household_finance/
  family_office/
  retirement_tracking/
  tax_pack/
```

Each workspace has its own config set and DB path.

This directly supports your “any number of personal finances” requirement.

---

# 14. Example Configuration Shape

Here is a representative config shape.

```yaml
project:
  name: household_finance
  database_path: ./data/warehouse/household_finance.db
  timezone: Asia/Kolkata

sources:
  - name: broker_transactions_folder
    kind: file_folder
    discoverer:
      plugin: latest_modified_file
      options:
        path: ./data/raw/broker_a
        recursive: true
        patterns: ["*.csv", "*.xlsx"]
    reader:
      plugin: auto_file_reader
    processing_strategy: transform_then_append

  - name: market_data_folder
    kind: file_folder
    discoverer:
      plugin: all_files
      options:
        path: ./data/raw/market_data
        recursive: true
        patterns: ["*.parquet"]
    reader:
      plugin: parquet_reader
    processing_strategy: raw_then_transform

  - name: legacy_sqlite_budget
    kind: sqlite_query
    connection:
      database_path: ./data/raw/legacy_budget.db
    query:
      sql: "select * from expenses"
    reader:
      plugin: sqlite_query_reader
    processing_strategy: single_asset

tables:
  - name: investment_transactions
    kind: base
    source_bindings: [broker_transactions_folder]
    primary_key:
      strategy: natural_key_hash
      fields:
        - account_id
        - transaction_date
        - isin
        - transaction_type
        - units
        - amount_minor
    columns:
      - name: account_id
        type: str
        required: true
        source_aliases: ["account", "acct_no"]
      - name: transaction_date
        type: date
        required: true
        source_aliases: ["date", "txn_date"]
      - name: isin
        type: str
        required: false
      - name: amount_minor
        type: int
        required: true
      - name: raw_description
        type: str
        required: false
    transforms:
      - type: rename_columns
      - type: trim_whitespace
      - type: parse_dates
      - type: normalize_money_to_minor_units
      - type: custom_plugin
        plugin: my_plugins.finance.normalize_broker_txn
    load:
      mode: upsert
      record_hash: true
    semantic:
      enabled: true
      narrative_template: investment_transaction_v1

derived_tables:
  - name: portfolio_analysis
    kind: derived
    engine: sql
    depends_on:
      - investment_transactions
      - market_prices
      - benchmark_master
      - benchmark_prices
    materialization: replace_table
    sql_template: portfolio_analysis_v1.sql
    semantic:
      enabled: true
      narrative_template: portfolio_analysis_summary_v1
```

---

# 15. Layered Package Structure

You asked for this exact layered architecture:

- `config`
- `domain`
- `contracts`
- `infrastructure`
- `etl`
- `tables`
- `semantic`
- `ui`

Below is the recommended package structure aligned to that.

```text
src/semantic_finance_etl/
│
├── config/
│   ├── models/
│   │   ├── app_config.py
│   │   ├── project_config.py
│   │   ├── source_config.py
│   │   ├── table_config.py
│   │   ├── column_config.py
│   │   ├── derived_table_config.py
│   │   ├── semantic_config.py
│   │   └── plugin_config.py
│   ├── loader.py
│   ├── merger.py
│   ├── resolver.py
│   └── compiler.py
│
├── domain/
│   ├── enums.py
│   ├── metadata.py
│   ├── runtime_schema.py
│   ├── finance_types.py
│   ├── semantic_metadata.py
│   ├── system_models/
│   │   ├── etl_run.py
│   │   ├── source_asset.py
│   │   ├── dead_letter.py
│   │   ├── lineage_record.py
│   │   ├── load_result.py
│   │   ├── schema_catalog.py
│   │   ├── semantic_document.py
│   │   └── embedding_record.py
│   └── value_objects/
│       ├── money.py
│       ├── fingerprint.py
│       ├── canonical_key.py
│       └── record_hash.py
│
├── contracts/
│   ├── source_discoverer.py
│   ├── source_reader.py
│   ├── transform_step.py
│   ├── validator.py
│   ├── table_loader.py
│   ├── schema_compiler.py
│   ├── runtime_model_factory.py
│   ├── key_generator.py
│   ├── hasher.py
│   ├── run_tracker.py
│   ├── dlq_writer.py
│   ├── lineage_recorder.py
│   ├── derived_table_builder.py
│   ├── narrative_builder.py
│   ├── embedding_provider.py
│   ├── vector_index.py
│   └── plugin_registry.py
│
├── infrastructure/
│   ├── db/
│   │   ├── sqlite_connection.py
│   │   ├── sqlite_schema_compiler.py
│   │   ├── sqlite_migrator.py
│   │   ├── sqlite_loader.py
│   │   ├── sqlite_run_tracker.py
│   │   ├── sqlite_dlq_writer.py
│   │   ├── sqlite_lineage_recorder.py
│   │   ├── sqlite_fts.py
│   │   └── sqlite_vec.py
│   ├── discovery/
│   │   ├── all_files_discoverer.py
│   │   ├── latest_modified_discoverer.py
│   │   ├── latest_created_discoverer.py
│   │   ├── recursive_folder_discoverer.py
│   │   ├── unprocessed_files_discoverer.py
│   │   └── sql_query_discoverer.py
│   ├── readers/
│   │   ├── csv_reader.py
│   │   ├── excel_reader.py
│   │   ├── parquet_reader.py
│   │   ├── json_reader.py
│   │   ├── sqlite_reader.py
│   │   ├── sql_reader.py
│   │   └── auto_reader.py
│   ├── transforms/
│   │   ├── polars_steps/
│   │   │   ├── rename_columns.py
│   │   │   ├── cast_types.py
│   │   │   ├── parse_dates.py
│   │   │   ├── normalize_money.py
│   │   │   ├── trim_strings.py
│   │   │   ├── deduplicate.py
│   │   │   └── derive_columns.py
│   │   └── plugin_loader.py
│   ├── hashing/
│   │   ├── file_fingerprint_service.py
│   │   ├── record_hasher.py
│   │   └── canonical_key_generator.py
│   ├── models/
│   │   └── runtime_model_factory.py
│   ├── derived/
│   │   ├── sql_derived_builder.py
│   │   ├── polars_derived_builder.py
│   │   └── dag_executor.py
│   └── semantic/
│       ├── template_narrative_builder.py
│       ├── sentence_transformer_provider.py
│       ├── semantic_index_service.py
│       └── hybrid_search_service.py
│
├── etl/
│   ├── orchestration/
│   │   ├── etl_engine.py
│   │   ├── run_context.py
│   │   ├── execution_plan.py
│   │   └── execution_planner.py
│   ├── services/
│   │   ├── source_discovery_service.py
│   │   ├── schema_sync_service.py
│   │   ├── validation_service.py
│   │   ├── load_service.py
│   │   ├── derived_refresh_service.py
│   │   └── semantic_refresh_service.py
│   ├── validation/
│   │   ├── row_validator.py
│   │   └── validation_result.py
│   ├── dlq/
│   │   └── dead_letter_router.py
│   └── lineage/
│       └── lineage_service.py
│
├── tables/
│   ├── pipeline/
│   │   ├── configured_table_pipeline.py
│   │   ├── configured_derived_pipeline.py
│   │   ├── pipeline_result.py
│   │   └── processing_strategy.py
│   ├── registry/
│   │   ├── table_registry.py
│   │   └── dependency_graph.py
│   └── templates/
│       ├── finance/
│       │   ├── transactions_template.py
│       │   ├── investment_transactions_template.py
│       │   └── market_prices_template.py
│       └── analytics/
│           └── portfolio_analysis_template.py
│
├── semantic/
│   ├── documents/
│   │   ├── document_builder.py
│   │   └── chunker.py
│   ├── indexing/
│   │   ├── fts_index_manager.py
│   │   └── vec_index_manager.py
│   ├── query/
│   │   ├── search_request.py
│   │   ├── hybrid_search.py
│   │   └── reranker.py
│   └── templates/
│       └── finance_narratives.py
│
├── ui/
│   ├── app.py
│   ├── controllers/
│   │   ├── config_controller.py
│   │   ├── run_controller.py
│   │   └── schema_controller.py
│   ├── views/
│   │   ├── workspace_view.py
│   │   ├── source_editor_view.py
│   │   ├── table_editor_view.py
│   │   ├── run_monitor_view.py
│   │   └── semantic_search_view.py
│   └── presenters/
│       └── run_presenter.py
│
└── bootstrap/
    ├── container.py
    └── app_factory.py
```

---

# 16. Core Abstractions

These are the key interfaces the whole system will stand on.

## 16.1 `SourceDiscoverer`

Purpose:
- discover eligible assets for a source config

Input:
- `SourceConfig`
- `RunContext`

Output:
- list of `DiscoveredAsset`

## 16.2 `SourceReader`

Purpose:
- read a discovered asset into a tabular representation

Output:
- `pl.LazyFrame` preferred
- or staged DataFrame convertible to Polars

## 16.3 `TransformStep`

Purpose:
- apply one transformation step

Examples:
- rename columns
- cast types
- parse dates
- normalize amount fields
- compute derived columns
- custom plugin transformation

## 16.4 `RuntimeModelFactory`

Purpose:
- turn `TableConfig` into runtime Pydantic model

This is one of the most important abstractions in the whole system.

## 16.5 `SchemaCompiler`

Purpose:
- turn runtime Pydantic model into SQLite DDL and schema metadata

## 16.6 `KeyGenerator`

Purpose:
- create deterministic `canonical_id`

## 16.7 `Hasher`

Purpose:
- create `record_hash`

## 16.8 `Validator`

Purpose:
- validate transformed rows against runtime Pydantic model

## 16.9 `TableLoader`

Purpose:
- perform UPSERT / replace / append load into SQLite

## 16.10 `DerivedTableBuilder`

Purpose:
- build config-defined derived tables from dependency tables

Engines:
- SQL
- Polars
- Python plugin

## 16.11 `NarrativeBuilder`

Purpose:
- convert structured data into semantic text documents

## 16.12 `EmbeddingProvider`

Purpose:
- generate local embeddings

## 16.13 `VectorIndex`

Purpose:
- store/query vectors via sqlite-vec

## 16.14 `RunTracker`

Purpose:
- track ETL runs, statuses, counts, timing

## 16.15 `DLQWriter`

Purpose:
- persist invalid rows and errors

## 16.16 `LineageRecorder`

Purpose:
- persist source-to-table-to-row lineage

---

# 17. ETL Execution Lifecycle

A full run should look like this.

## 17.1 Bootstrapping
1. load workspace config
2. validate config
3. compile runtime schemas
4. connect SQLite
5. synchronize schema
6. start ETL run

## 17.2 Base table ingestion
For each source-bound base table:

1. execute discoverer
2. fingerprint assets
3. skip unchanged if idempotency says so
4. read source data
5. apply processing strategy
6. transform using Polars/plugin steps
7. generate canonical keys
8. generate record hashes
9. validate against runtime Pydantic model
10. route invalid rows to DLQ
11. load valid rows into SQLite
12. write lineage
13. record pipeline metrics

## 17.3 Derived table processing
1. build dependency DAG
2. topologically sort
3. execute derived tables in order
4. materialize outputs
5. register lineage and version info

## 17.4 Semantic refresh
1. select semantic-enabled tables
2. create narratives
3. update FTS5
4. generate embeddings
5. update sqlite-vec

## 17.5 Completion
1. finalize ETL run
2. persist summary
3. expose results to UI / CLI

---

# 18. SQL Generation Strategy

You asked for the engine mindset to be explained properly.

Even in a Polars-first ETL, SQL generation is still central because SQLite is the durable serving layer.

At minimum, the engine should generate SQL in three places.

## 18.1 DDL generation

From runtime Pydantic models, generate:

- `CREATE TABLE`
- `CREATE INDEX`
- `CREATE VIRTUAL TABLE ... USING fts5`
- vector index support tables

Example responsibility:
- convert `str -> TEXT`
- `int -> INTEGER`
- `date -> TEXT`
- nullable and required behavior
- unique constraints from config

## 18.2 UPSERT generation

For idempotent loads, the engine should generate SQL like:

- `INSERT ... ON CONFLICT (...) DO UPDATE`

This is the main load operation.

That gives you:
- insert new rows
- update changed rows
- skip unchanged records based on `record_hash`

## 18.3 Derived analytical SQL generation

For derived tables, the engine should generate SQL using at least these operations:

### Operation 1: `JOIN`
Used to combine base tables.

Example:
- join `investment_transactions` with `market_prices`
- join portfolio facts with benchmark metadata

### Operation 2: `GROUP BY`
Used to aggregate performance metrics.

Example:
- group cash flows by account / instrument / date
- aggregate invested amount, units, gains

### Operation 3: window functions
Used for:
- running balances
- ranking
- period return calculations
- latest price selection

### Operation 4: UPSERT / replace materialization
Used to publish the analytical output table.

## Example derived-table SQL flow

For `portfolio_analysis`, conceptually:

1. `JOIN` investment transactions with market prices
2. `JOIN` benchmark mappings
3. `GROUP BY` portfolio and valuation date
4. compute totals and returns
5. write to `portfolio_analysis`

That means the engine is not only generating DDL; it is also generating **load SQL** and **analytical SQL**.

---

# 19. Transformation Architecture

## 19.1 Prefer declarative transforms first

Built-in transform specs should cover most common needs:

- rename
- select
- reorder
- cast
- fill nulls
- trim
- regex replace
- parse date
- parse decimal
- normalize currency
- split columns
- concat columns
- derive conditional columns
- dedupe
- sort
- filter

## 19.2 Use plugin transforms for hard cases

For messy broker exports and weird Excel layouts, config alone will not always be enough.

Allow:

- module path + callable name in config
- plugin receives `LazyFrame`, config, run context
- plugin returns `LazyFrame`

## 19.3 Excel parsing reality

You already called this correctly.

For messy Excel:
- use `pandas` or `fastexcel` when spatial parsing is required
- convert to Polars as early as possible
- keep Excel-specific ugliness inside reader/parser layer only

---

# 20. UI Architecture

The UI should be a thin orchestration/configuration layer.

It must not contain business logic.

## UI responsibilities
- create/edit workspace config
- manage sources
- manage table definitions
- preview mappings
- run ETL
- monitor runs
- inspect DLQ
- trigger semantic refresh
- browse schema metadata

## UI should call
- application services
- ETL engine services
- config services

## UI should not do
- transformation logic
- SQL generation
- Pydantic model building
- direct DB mutation outside application services

---

# 21. Recommended Build Order

You asked to go step by step from architecture, then package structure, then core abstractions.

This is the right sequence.

## Phase 1 — Foundation architecture
Build first:

- package structure
- config models
- system domain models
- runtime model factory concept
- schema compiler concept
- SQLite connection/init
- ETL run tracker
- source asset tracker
- DLQ table

## Phase 2 — Config compiler
Build:

- workspace config loading
- config validation
- config merge/resolution
- table config compilation
- runtime Pydantic model generation

## Phase 3 — Discovery and reading
Build:

- discoverer contracts
- file discoverers
- source fingerprinting
- CSV/JSON/parquet/SQLite readers
- Excel reader abstraction

## Phase 4 — Generic configured pipeline
Build:

- `ConfiguredTablePipeline`
- transform step chain
- validator
- loader
- idempotent UPSERT

## Phase 5 — Derived table engine
Build:

- dependency graph
- SQL derived builder
- Polars derived builder
- materialization modes

## Phase 6 — Semantic layer
Build:

- semantic document generation
- FTS5
- local embeddings
- sqlite-vec
- hybrid search

## Phase 7 — UI
Build:

- workspace editor
- source editor
- table editor
- run monitor
- DLQ viewer

---

# 22. First Milestone Recommendation

Given your current goal, I would define **Milestone 1** like this:

## Milestone 1
**Config-driven schema foundation**

Deliverables:

- package structure
- config models
- static system Pydantic models
- runtime business model factory
- SQLite schema compiler
- schema sync service
- ETL run table
- source asset table
- DLQ table
- metadata catalog tables

This milestone should **not yet** include:

- full Excel parsing complexity
- all discoverer plugins
- semantic embeddings
- complex derived tables
- UI

But it must be designed so those fit naturally next.

---

# 23. Architecture Decisions Summary

## Decision 1
The application is an **ETL engine**, not a hardcoded finance app.

## Decision 2
Business tables are **config-defined**, not code-defined.

## Decision 3
Pydantic remains the source of truth via:
- static system models
- runtime-generated business models

## Decision 4
Source discovery is a **plugin subsystem**, not a folder scan utility.

## Decision 5
Processing strategy is configurable:
- latest file
- all files
- raw then transform
- transform then append
- single asset
- snapshot replace
- incremental upsert

## Decision 6
Derived tables are first-class citizens with dependency DAG support.

## Decision 7
Semantic indexing includes both base and analytical tables.

## Decision 8
UI edits config and triggers services; it does not host business logic.

---
