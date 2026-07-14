# `semantic-finance-ETL` v2 Design Document  

# 1. Executive Summary

`semantic-finance-ETL` will be a **local-first Python ETL application** that ingests personal finance data from local files and local databases, transforms it through modular table pipelines, validates it using Pydantic, and loads it into a semantically rich SQLite warehouse.

It is designed to serve two use cases:

1. **Power BI today**
   - standardized finance tables
   - clean dimensions/facts
   - lineage and auditability
   - idempotent refreshes

2. **Local AI agents tomorrow**
   - semantic metadata
   - FTS5 keyword search
   - sqlite-vec vector search
   - local sentence-transformer embeddings
   - narrative/context enrichment

The revised architecture is now explicitly:

- **configuration-driven**
- **plugin-based**
- **schema-flexible**
- **source-flexible**
- **discovery-flexible**
- **table-pipeline-driven**
- **UI-configurable**

---

# 2. What Changes from the Existing Design Doc

Your requested changes imply these architecture upgrades:

## 2.1 Expanded source support
The system must support:

- `.xlsx`
- `.xls`
- `.csv`
- `.tsv`
- `.json`
- `.jsonl`
- `.parquet`
- `.sqlite`
- local SQL sources
- SQL query-based extraction from local databases
- future local connectors like DuckDB / PostgreSQL / MySQL / SQL Server, as long as they are local and not cloud-hosted

## 2.2 Discovery must become a first-class plugin system
You do **not** just need readers.  
You need a layer before readers:

```text
discover -> select -> group -> read -> transform -> validate -> load
```

This is critical because the same folder can be processed in different ways:

- latest file only
- latest N files
- all files
- files since last successful batch
- unprocessed files only
- files matching pattern
- files partitioned by month/account/broker
- transform each file then append
- append raw first then transform once

## 2.3 Configuration must drive the entire system
You want the app to behave like a local ETL platform:

- add a new source by editing config
- change database path by editing config
- add column mappings by editing config
- change append/discovery behavior by editing config
- add a new finance table by editing config + implementing a pipeline
- UI should create/edit/save config and trigger the batch

That means config is not a side utility. It is the **control plane** of the whole application.

---

# 3. Core Architectural Principles

These principles should govern every design decision.

## 3.1 Local-first and private by design
Everything runs locally:

- local filesystem
- local SQLite database
- local embeddings
- local vector search
- no cloud APIs
- no hosted DBs

## 3.2 Pydantic is the schema source of truth
Pydantic models define:

- canonical row structure
- validation rules
- field constraints
- semantic metadata
- DB schema generation inputs

We do **not** maintain `schema.sql` as the primary truth.

## 3.3 Config-driven orchestration
The ETL engine should be runnable with:

```text
load config -> discover sources -> build jobs -> run pipelines -> load DB
```

without hardcoding paths, readers, or mappings.

## 3.4 Plugin-based extensibility
The system must support independent extension points for:

- source discovery
- source readers
- table pipelines
- transformations
- validation rules
- key generation
- semantic enrichment
- UI editors

## 3.5 Idempotent and auditable by default
Every run must be traceable and repeat-safe through:

- file fingerprints
- batch tracking
- source lineage
- canonical IDs
- record hashes
- UPSERT logic
- dead letter queues

## 3.6 Clear layering and dependency inversion
Business logic should not depend directly on SQLite or Excel specifics.  
Infrastructure implements contracts; orchestration depends on abstractions.

---

# 4. Revised Layered Architecture

You asked for this package layout:

- `config`
- `domain`
- `contracts`
- `infrastructure`
- `etl`
- `tables`
- `semantic`
- `ui`

That is a good architecture for this project. I would formalize it like this:

```text
ui
  -> etl application services
  -> config services

etl
  -> contracts
  -> domain
  -> config

tables
  -> contracts
  -> domain

semantic
  -> contracts
  -> domain
  -> infrastructure adapters

infrastructure
  -> contracts
  -> domain
  -> config

contracts
  -> domain only

config
  -> domain-safe Pydantic configuration models

domain
  -> pure canonical models, enums, metadata, rules
```

## 4.1 Layer responsibilities

| Layer | Responsibility |
|---|---|
| `config` | Pydantic config models, config loading, config validation, config merging |
| `domain` | Canonical finance entities, enums, semantic metadata, field specs |
| `contracts` | Abstract interfaces and protocols for readers, discoverers, loaders, repositories, services |
| `infrastructure` | SQLite engine, file readers, SQL connectors, hashing, parsers, filesystem adapters |
| `etl` | Run orchestration, lineage, validation, DLQ, execution services, scheduler hooks |
| `tables` | One pipeline per target table, table-specific mapping/transform/validation/load behavior |
| `semantic` | narratives, embedding generation, FTS5, sqlite-vec, hybrid retrieval |
| `ui` | CustomTkinter config editor, batch runner, run monitor, DLQ viewer |

## 4.2 Why this structure is stronger than a generic “application/infrastructure” split
Because your project is not just ETL. It is:

- ETL platform
- schema manager
- local semantic layer
- desktop-operated config engine

So having distinct `tables`, `semantic`, and `ui` packages is cleaner than hiding everything in a generic `application` folder.

---

# 5. High-Level Runtime Flow

The end-to-end runtime should look like this:

```text
1. Load app config
2. Validate config with Pydantic
3. Initialize plugin registries
4. Initialize SQLite + schema synchronization
5. Discover source files / source datasets
6. Build source jobs from config
7. Route each source job to the target table pipeline
8. Extract data using source reader
9. Apply source mappings and table transformations
10. Validate canonical rows with Pydantic
11. Route invalid rows to DLQ
12. UPSERT valid rows into SQLite
13. Update lineage, file manifest, and batch tracking
14. Refresh FTS5 / vector indexes if configured
15. Expose data to Power BI / future UI / local agent services
```

---

# 6. Core Platform Concepts

The architecture becomes much clearer if you separate these concepts.

## 6.1 `Source`
A configured input definition. Example:

- HDFC credit card exports
- Zerodha holdings folder
- one SQLite table export
- one local PostgreSQL query
- one folder of monthly CSV statements

## 6.2 `Discoverer`
Finds physical inputs for a source. Example:

- latest file in folder
- all files in folder
- all unprocessed files
- all matching partitions

## 6.3 `Reader`
Reads the physical input. Example:

- CSV reader
- Excel reader
- Parquet reader
- JSON reader
- SQLite query reader
- local SQL reader

## 6.4 `Source Group`
A logical unit of processing composed of one or more discovered items.

Examples:

- all monthly brokerage CSVs for one run
- only latest statement file
- all new files since last run
- all files in one account folder

## 6.5 `Table Pipeline`
Owns business logic for one canonical target table.

Examples:

- `TransactionsPipeline`
- `AccountsPipeline`
- `InvestmentTransactionsPipeline`
- `HoldingsSnapshotPipeline`
- `MarketPricesPipeline`

## 6.6 `Canonical Model`
Pydantic model describing the target row shape and rules.

## 6.7 `Batch`
A single ETL execution instance.

## 6.8 `Dead Letter Record`
A rejected row with reason, lineage, and raw payload.

---

# 7. Package Structure

Here is the recommended package structure aligned to your required architecture.

```text
semantic_finance_etl/
│
├── config/
│   ├── models/
│   │   ├── app_config.py
│   │   ├── database_config.py
│   │   ├── source_config.py
│   │   ├── discovery_config.py
│   │   ├── reader_config.py
│   │   ├── table_config.py
│   │   ├── mapping_config.py
│   │   ├── pipeline_config.py
│   │   ├── semantic_config.py
│   │   └── ui_config.py
│   ├── loader.py
│   ├── merger.py
│   ├── resolver.py
│   └── defaults.py
│
├── domain/
│   ├── base.py
│   ├── enums.py
│   ├── metadata.py
│   ├── finance/
│   │   ├── account.py
│   │   ├── transaction.py
│   │   ├── category.py
│   │   ├── merchant.py
│   │   ├── investment_transaction.py
│   │   ├── instrument.py
│   │   ├── holding_snapshot.py
│   │   ├── market_price.py
│   │   └── portfolio.py
│   ├── lineage/
│   │   ├── source_file.py
│   │   ├── batch_run.py
│   │   ├── file_fingerprint.py
│   │   └── dead_letter.py
│   └── semantic/
│       ├── searchable_document.py
│       ├── embedding_record.py
│       └── narrative_fragment.py
│
├── contracts/
│   ├── config_provider.py
│   ├── source_discoverer.py
│   ├── source_reader.py
│   ├── table_pipeline.py
│   ├── transformer.py
│   ├── validator.py
│   ├── loader.py
│   ├── repository.py
│   ├── hash_provider.py
│   ├── key_generator.py
│   ├── sql_schema_builder.py
│   ├── embedding_provider.py
│   └── search_provider.py
│
├── infrastructure/
│   ├── database/
│   │   ├── sqlite_connection.py
│   │   ├── sqlite_pragma.py
│   │   ├── sqlite_schema_sync.py
│   │   ├── sqlite_repository.py
│   │   ├── sqlite_upsert_writer.py
│   │   ├── sqlite_fts5.py
│   │   ├── sqlite_vec.py
│   │   └── migrations.py
│   ├── discovery/
│   │   ├── local_file_discoverer.py
│   │   ├── latest_file_discoverer.py
│   │   ├── all_files_discoverer.py
│   │   ├── unprocessed_files_discoverer.py
│   │   ├── partition_discoverer.py
│   │   └── sql_source_discoverer.py
│   ├── readers/
│   │   ├── csv_reader.py
│   │   ├── excel_reader.py
│   │   ├── parquet_reader.py
│   │   ├── json_reader.py
│   │   ├── sqlite_reader.py
│   │   ├── sql_query_reader.py
│   │   └── auto_reader.py
│   ├── parsers/
│   │   ├── messy_excel_parser.py
│   │   ├── header_detector.py
│   │   ├── range_extractor.py
│   │   └── column_normalizer.py
│   ├── hashing/
│   │   ├── sha256_hash_provider.py
│   │   ├── file_fingerprint_service.py
│   │   └── record_hash_service.py
│   ├── mappings/
│   │   ├── yaml_mapping_loader.py
│   │   └── mapping_resolver.py
│   ├── registry/
│   │   ├── discoverer_registry.py
│   │   ├── reader_registry.py
│   │   ├── pipeline_registry.py
│   │   └── semantic_registry.py
│   └── semantic/
│       ├── sentence_transformer_provider.py
│       ├── embedding_cache.py
│       ├── hybrid_search_service.py
│       └── narrative_builder.py
│
├── etl/
│   ├── models/
│   │   ├── discovered_item.py
│   │   ├── source_group.py
│   │   ├── extract_result.py
│   │   ├── transform_result.py
│   │   ├── validate_result.py
│   │   ├── load_result.py
│   │   └── pipeline_run_result.py
│   ├── orchestration/
│   │   ├── etl_runner.py
│   │   ├── batch_orchestrator.py
│   │   ├── source_job_builder.py
│   │   ├── pipeline_executor.py
│   │   └── semantic_refresh_orchestrator.py
│   ├── services/
│   │   ├── batch_service.py
│   │   ├── manifest_service.py
│   │   ├── lineage_service.py
│   │   ├── dlq_service.py
│   │   ├── schema_service.py
│   │   ├── plugin_service.py
│   │   └── config_run_service.py
│   └── policies/
│       ├── append_strategy.py
│       ├── validation_policy.py
│       ├── retry_policy.py
│       └── idempotency_policy.py
│
├── tables/
│   ├── common/
│   │   ├── base_pipeline.py
│   │   ├── base_transformer.py
│   │   ├── canonical_mapper.py
│   │   └── column_mapping_applier.py
│   ├── transactions/
│   │   ├── pipeline.py
│   │   ├── model.py
│   │   ├── key_generator.py
│   │   └── rules.py
│   ├── accounts/
│   │   ├── pipeline.py
│   │   └── model.py
│   ├── investment_transactions/
│   │   ├── pipeline.py
│   │   ├── model.py
│   │   ├── key_generator.py
│   │   └── rules.py
│   ├── holdings_snapshot/
│   │   ├── pipeline.py
│   │   └── model.py
│   ├── market_prices/
│   │   ├── pipeline.py
│   │   └── model.py
│   └── merchants/
│       ├── pipeline.py
│       └── model.py
│
├── semantic/
│   ├── models/
│   │   ├── semantic_document.py
│   │   ├── search_result.py
│   │   └── narrative_config.py
│   ├── services/
│   │   ├── semantic_index_service.py
│   │   ├── embedding_service.py
│   │   ├── keyword_search_service.py
│   │   ├── vector_search_service.py
│   │   └── hybrid_search_service.py
│   └── builders/
│       ├── transaction_narrative_builder.py
│       └── investment_narrative_builder.py
│
├── ui/
│   ├── app.py
│   ├── windows/
│   │   ├── main_window.py
│   │   ├── config_editor_window.py
│   │   ├── source_manager_window.py
│   │   ├── pipeline_runner_window.py
│   │   ├── run_history_window.py
│   │   └── dlq_viewer_window.py
│   ├── viewmodels/
│   │   ├── app_viewmodel.py
│   │   ├── config_viewmodel.py
│   │   └── run_viewmodel.py
│   └── widgets/
│       ├── source_form.py
│       ├── mapping_editor.py
│       └── run_log_panel.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   └── fixtures/
│
├── pyproject.toml
├── README.md
└── .gitignore
```

---

# 8. Supported Source Types

This needs to be explicit because source diversity is central to your design.

## 8.1 File-based sources
- CSV
- TSV
- XLSX
- XLS
- JSON
- JSONL
- Parquet
- SQLite database file
- future: XML, fixed-width text, OFX/QIF, broker PDFs through optional extraction layer

## 8.2 Local SQL sources
Supported only if they are local/private:

- SQLite
- DuckDB
- local PostgreSQL
- local MySQL
- local SQL Server
- any local SQL source reachable through a local driver

## 8.3 SQL extraction modes
For SQL sources, config should allow:

- whole table extraction
- custom query extraction
- incremental extraction using watermark fields
- partitioned extraction

Examples:

```text
SELECT * FROM transactions
```

or

```text
SELECT account_id, txn_date, amount, description
FROM bank_transactions
WHERE txn_date >= :from_date
```

---

# 9. Source Discovery Plugin Architecture

This is one of the most important additions.

## 9.1 Why discovery should be separate from reading
A reader answers:

> “How do I read this file/database object?”

A discoverer answers:

> “Which files or datasets should I process right now?”

Those are different responsibilities and should stay separate.

## 9.2 Discoverer interface
Each discoverer plugin should implement a common contract conceptually like:

```text
discover(source_config, runtime_context) -> list[DiscoveredItem]
```

## 9.3 Recommended built-in discoverers

| Discoverer | Use case |
|---|---|
| `AllFilesDiscoverer` | process every matching file |
| `LatestModifiedFileDiscoverer` | process only most recently modified file |
| `LatestCreatedFileDiscoverer` | process most recently created file |
| `LatestNFilesDiscoverer` | process latest N files |
| `UnprocessedFilesDiscoverer` | process only files not previously loaded |
| `ChangedFilesDiscoverer` | process only files whose content hash changed |
| `PatternBasedDiscoverer` | process files matching include/exclude patterns |
| `PartitionDiscoverer` | process files grouped by partition key |
| `DateWindowDiscoverer` | process files in a date interval |
| `ManualSelectionDiscoverer` | UI-selected files only |
| `SqlDatasetDiscoverer` | for SQL sources, produces logical datasets instead of file paths |

## 9.4 Grouping behaviors
Discovery should support grouping into `SourceGroup`s:

- all files together
- one file per group
- one month per group
- one account per group
- one broker per group
- one SQL partition per group

This is important because **discovery output determines pipeline execution strategy**.

---

# 10. Append and Processing Strategies

You mentioned flexibility around:

- transform after appending
- append after transforming
- judge case by case

This should be formalized as an append/processing policy.

## 10.1 Recommended processing modes

### `SINGLE_FILE`
Process one discovered file at a time.

Use for:
- latest statement only
- independent source files
- highly irregular Excel layouts

### `RAW_THEN_TRANSFORM`
Read all source files first, append raw rows, then transform one consolidated dataset.

Use for:
- same schema across files
- monthly CSV dumps
- homogeneous exports

Pipeline:

```text
discover -> read all -> append raw -> transform -> validate -> load
```

### `TRANSFORM_THEN_APPEND`
Transform each file individually into canonical structure, then append canonical rows.

Use for:
- multiple layouts
- header drift
- messy Excel
- broker/vendor differences

Pipeline:

```text
discover -> read one -> transform one -> validate one -> append canonical -> load
```

### `PARTITIONED_BATCH`
Process by partition group.

Use for:
- one pipeline per month/account/broker
- large datasets
- incremental control

## 10.2 Decision rule
This must be configuration-driven, not hardcoded.

---

# 11. Configuration-Driven Architecture

This is the control center of the platform.

## 11.1 Config design goals
Config must allow you to define:

- app-level settings
- SQLite path
- semantic settings
- source definitions
- discovery behavior
- file patterns
- reader type
- target table
- column mapping
- transformations
- append strategy
- validation behavior
- load behavior
- post-load semantic refresh

## 11.2 Config should be editable by both code and UI
That means config must be:

- structured
- validated
- serializable
- round-trippable
- modular

Best format options:

- YAML for readability
- TOML for strong structure
- JSON for programmatic editing

My recommendation:

- **YAML for user-facing project config**
- Pydantic models for internal validation
- UI edits YAML through strongly typed Pydantic-backed forms

## 11.3 Recommended config layers

### `app.yaml`
Global system settings.

### `sources/`
One file per source definition.

### `tables/`
Optional table-level pipeline defaults.

### `mappings/`
Reusable column mapping definitions.

### `profiles/`
Optional user profiles or environment profiles.

This is better than one giant config file because it stays maintainable.

## 11.4 Example config structure

```yaml
app:
  name: semantic-finance-etl
  database:
    sqlite_path: data/warehouse/finance.db
    enable_fts5: true
    enable_sqlite_vec: true
    pragmas:
      journal_mode: WAL
      synchronous: NORMAL

  semantic:
    embedding_model: all-MiniLM-L6-v2
    embedding_batch_size: 128
    rebuild_on_load: false

  runtime:
    fail_fast: false
    max_workers: 4
    timezone: America/New_York

sources:
  - name: hdfc_credit_card_statements
    enabled: true
    source_type: file
    target_table: transactions
    pipeline: transactions
    discoverer:
      type: latest_modified_file
      path: data/raw/cards/hdfc
      recursive: true
      include_patterns: ["*.csv", "*.xlsx"]
      exclude_patterns: ["~$*", "*.tmp"]
    reader:
      type: auto
      options:
        sheet_name: null
        header_row_strategy: detect
    processing:
      mode: transform_then_append
      group_by: none
    mappings:
      file: mappings/hdfc_transactions.yaml
    load:
      mode: upsert
      unique_key_strategy: pipeline_default
    semantic:
      build_narratives: true

  - name: zerodha_holdings_exports
    enabled: true
    source_type: file
    target_table: holdings_snapshot
    pipeline: holdings_snapshot
    discoverer:
      type: all_files
      path: data/raw/investments/zerodha
      recursive: true
      include_patterns: ["*.xlsx"]
    reader:
      type: excel
      options:
        sheet_name: Holdings
        header_row_strategy: explicit
        header_row_index: 4
    processing:
      mode: raw_then_transform
      group_by: month
    mappings:
      file: mappings/zerodha_holdings.yaml

  - name: local_sqlite_cashbook
    enabled: true
    source_type: sqlite
    target_table: transactions
    pipeline: transactions
    discoverer:
      type: sql_dataset
    reader:
      type: sqlite_query
      options:
        database_path: data/raw/sqlite/cashbook.db
        query: |
          SELECT account_name, txn_date, description, amount, category
          FROM transactions
    processing:
      mode: single_file
```

## 11.5 Why this matters
With this model, adding a new source usually becomes:

1. add source config
2. add mapping config
3. point to an existing pipeline  
or
4. create a new table pipeline if truly new

That is the correct level of modularity for your use case.

---

# 12. Config Model Hierarchy

These should be Pydantic config models under `config/models`.

## 12.1 Core config models
- `AppConfig`
- `DatabaseConfig`
- `RuntimeConfig`
- `SemanticConfig`
- `SourceConfig`
- `DiscoveryConfig`
- `ReaderConfig`
- `ProcessingConfig`
- `LoadConfig`
- `MappingConfig`
- `TableConfig`
- `UIConfig`

## 12.2 Important config validation rules
Examples:

- `sqlite_path` must not be empty
- discoverer type must exist in registry
- reader type must exist in registry
- target table must exist in pipeline registry
- include patterns cannot be empty for file sources
- SQL query must exist for query readers
- partition key required for partition-based modes
- mapping file must exist if explicit mapping is referenced

---

# 13. Plugin System Design

The plugin system should stay simple but strong.

## 13.1 Plugin types
You need independent registries for:

- discoverers
- readers
- pipelines
- key generators
- semantic builders

## 13.2 Registration strategy
For a local-first personal project, start with **internal explicit registration**, not Python entry-point discovery.

That means something like this conceptually:

- `DiscovererRegistry.register("all_files", AllFilesDiscoverer)`
- `ReaderRegistry.register("csv", CsvReader)`
- `PipelineRegistry.register("transactions", TransactionsPipeline)`

Later you can add package entry-point support if you want external plugins.

## 13.3 Why explicit registry is better initially
Because it is:

- easier to debug
- easier to type-check
- easier to control
- better for early architecture stability

---

# 14. Domain Model Strategy

The domain layer should be pure and stable.

## 14.1 Domain categories

### Canonical finance entities
- `Account`
- `Transaction`
- `Category`
- `Merchant`
- `InvestmentTransaction`
- `Instrument`
- `HoldingSnapshot`
- `MarketPrice`
- `Portfolio`

### Lineage/audit entities
- `BatchRun`
- `SourceFile`
- `FileFingerprint`
- `DeadLetterRecord`

### Semantic entities
- `SearchableDocument`
- `EmbeddingRecord`
- `NarrativeFragment`

## 14.2 Pydantic model requirements
Every canonical table model should support:

- field metadata
- optional aliases
- type constraints
- semantic annotations
- business keys / natural keys
- deterministic canonical ID generation inputs
- record hashing inputs

---

# 15. Pydantic-Driven Schema Management

This is one of the strongest parts of the system.

## 15.1 Rule
Pydantic models define the schema. SQLite schema is derived from them.

## 15.2 What gets generated from Pydantic
From a canonical model, the system should derive:

- table name
- column names
- SQLite types
- nullability
- default values where safe
- indexes
- unique constraints
- FTS5 projection rules
- vector search projection rules
- metadata tables if needed

## 15.3 Schema sync behavior
At startup or batch run:

```text
load Pydantic models
compare model schema with SQLite schema
create missing tables
add missing columns where safe
create missing indexes
log incompatible changes
```

## 15.4 Important rule for schema evolution
Because SQLite has limited `ALTER TABLE` flexibility:

- additive changes are easy
- destructive changes must be migration-driven
- renames need explicit migration rules
- type changes need compatibility handling

## 15.5 Adding a new column
This directly addresses your modularity requirement.

If you want to add a new column to a table:

1. update the Pydantic model
2. update mapping config if needed
3. update table pipeline logic if needed
4. schema sync detects missing column
5. SQLite `ALTER TABLE ADD COLUMN` is generated
6. future loads populate it
7. historical backfill can be run separately if needed

That is exactly the behavior you want.

---

# 16. SQL Generation Strategy

You asked for engineering rigor, so this is important.

The app should generate SQL from schema metadata and load policies, rather than relying on hand-written SQL everywhere.

## 16.1 SQL operation 1: `CREATE TABLE`
When the app sees a new Pydantic model, it should generate a `CREATE TABLE` statement.

Example conceptually:

```sql
CREATE TABLE IF NOT EXISTS transactions (
    canonical_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    transaction_date TEXT NOT NULL,
    amount NUMERIC NOT NULL,
    currency TEXT,
    description TEXT,
    record_hash TEXT NOT NULL,
    source_file_id TEXT,
    created_batch_id TEXT NOT NULL,
    updated_batch_id TEXT NOT NULL
);
```

This SQL is not the source of truth.  
It is **generated from the Pydantic model**.

## 16.2 SQL operation 2: `INSERT ... ON CONFLICT DO UPDATE`
For idempotent loads, the system should generate UPSERT SQL.

Conceptually:

```sql
INSERT INTO transactions (
    canonical_id,
    account_id,
    transaction_date,
    amount,
    description,
    record_hash,
    source_file_id,
    created_batch_id,
    updated_batch_id
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(canonical_id) DO UPDATE SET
    account_id = excluded.account_id,
    transaction_date = excluded.transaction_date,
    amount = excluded.amount,
    description = excluded.description,
    record_hash = excluded.record_hash,
    updated_batch_id = excluded.updated_batch_id
WHERE transactions.record_hash <> excluded.record_hash;
```

This gives you:

- insert new rows
- update changed rows
- skip unchanged rows implicitly

## 16.3 SQL operation 3: `ALTER TABLE ADD COLUMN`
When the model evolves and a new field is added:

```sql
ALTER TABLE transactions ADD COLUMN merchant_city TEXT;
```

This should be generated only for safe additive changes.

## 16.4 SQL operation 4: `CREATE INDEX`
Indexes should be generated from model/table metadata.

Example:

```sql
CREATE INDEX IF NOT EXISTS idx_transactions_date
ON transactions (transaction_date);
```

This is useful for Power BI filters and local search.

---

# 17. Reader Architecture

Each reader should implement a common contract, but specialize by source type.

## 17.1 Reader families

### File readers
- CSV reader
- Excel reader
- Parquet reader
- JSON reader

### Database readers
- SQLite reader
- generic SQL query reader

### Auto reader
Chooses the reader based on:
- source type
- file extension
- config hint

## 17.2 Excel strategy
Excel is special because messy finance spreadsheets often require spatial parsing.

Use:

- `polars` for clean tabular reads where possible
- `pandas` or `fastexcel` only when needed
- custom sheet/range/header detection utilities for messy layouts

## 17.3 Reader output
Readers should not return raw pandas frames everywhere.  
Return a structured extraction object, e.g.:

- raw tabular data
- metadata
- sheet name
- source lineage
- parser notes

Internally this can hold:

- `pl.LazyFrame`
- `pl.DataFrame`
- temporary pandas DataFrame for Excel parsing
- raw JSON object list

---

# 18. Transformation Architecture

Transformation should be owned primarily by **table pipelines**, not by readers.

## 18.1 Separation of concerns
- reader: “what data exists?”
- mapping: “which source columns correspond to canonical columns?”
- transformer: “how do I normalize values?”
- validator: “is the canonical row valid?”
- loader: “how do I persist it?”

## 18.2 Use Polars as the default transformation engine
Especially for:

- filtering
- joins
- normalizing types
- aggregations
- deduplication
- column derivation
- lazy execution

## 18.3 Use pandas only when needed
Specifically for:
- messy Excel positional extraction
- odd merged cells
- inconsistent header blocks
- sheet sniffing

Then convert into Polars as early as possible.

---

# 19. Table Pipeline Architecture

This is the heart of the ETL system.

## 19.1 One table = one pipeline
Each canonical target table gets its own class-based pipeline.

Examples:

- `TransactionsPipeline`
- `AccountsPipeline`
- `InvestmentTransactionsPipeline`
- `HoldingsSnapshotPipeline`
- `MarketPricesPipeline`

## 19.2 Pipeline responsibilities
Each pipeline should own:

- source-specific extraction coordination
- column mapping application
- standardization logic
- canonical ID generation
- record hashing
- Pydantic validation
- load preparation
- DLQ routing rules

## 19.3 Pipeline lifecycle
For each source group:

```text
extract
-> transform
-> validate
-> split valid / invalid
-> load
-> record lineage
```

## 19.4 Why pipelines are better than generic transformations
Because finance tables have different semantics:

- transactions care about amount/date/description
- holdings snapshots care about snapshot date + instrument
- market prices care about instrument + price date
- investment transactions care about units/price/folio/type

A generic ETL function becomes messy very quickly.

---

# 20. Column Mapping Design

This is essential for configurability.

## 20.1 Column mapping should be externalized
Mappings should live in config files, not be hardcoded in pipeline classes.

Example mapping file:

```yaml
source_name: hdfc_credit_card_statements
target_table: transactions

columns:
  txn_date:
    target: transaction_date
    transforms: [parse_date_ddmmyyyy]

  details:
    target: description
    transforms: [strip, normalize_whitespace]

  amount_inr:
    target: amount
    transforms: [to_decimal]

  card_type:
    target: account_name
```

## 20.2 Why this matters
If a bank changes one column name, you should update a mapping file, not rewrite the codebase.

---

# 21. Deterministic Key Generation

You already recognized that many sources lack stable IDs.  
So every canonical table should support generated keys.

## 21.1 Two identifiers per row

### `canonical_id`
Represents business identity.

### `record_hash`
Represents row content state.

## 21.2 Example key strategies

| Table | Canonical key inputs |
|---|---|
| `transactions` | account + date + amount + description + reference/source |
| `investment_transactions` | account + folio + instrument + date + type + units + amount |
| `market_prices` | instrument + price_date + price_source + price_type |
| `holdings_snapshot` | account + instrument + snapshot_date |
| `accounts` | source_system + external_account_id or normalized account name |

## 21.3 Why both are needed
Because identity and content are not the same thing.

- `canonical_id` says whether it is the same business row
- `record_hash` says whether the stored values changed

---

# 22. Idempotency Strategy

This needs to exist at multiple levels.

## 22.1 File-level idempotency
Track:

- file path
- relative path
- file size
- modified timestamp
- content hash

This answers:

> “Have I processed this physical file before?”

## 22.2 Batch-level idempotency
Each ETL run gets a batch record:

- batch ID
- start time
- end time
- config version
- status
- source selection summary

## 22.3 Row-level idempotency
Use:

- `canonical_id`
- `record_hash`

## 22.4 Load-level idempotency
Use SQLite UPSERT with conflict detection.

## 22.5 DLQ idempotency
A bad row should not create uncontrolled duplicate dead letters on repeated runs.  
DLQ records should include a deterministic failure fingerprint.

---

# 23. Lineage and Audit Tables

This should be built in from the beginning.

## 23.1 Required lineage tables
- `etl_batch_runs`
- `source_files`
- `source_file_fingerprints`
- `dead_letter_queue`
- optional `etl_events`

## 23.2 Canonical tables should carry lineage metadata
Each row should generally include:

- `source_file_id`
- `created_batch_id`
- `updated_batch_id`
- optional `source_system`
- optional `raw_row_number`

This is extremely useful for:

- debugging
- DLQ tracing
- batch replay
- auditability
- Power BI lineage views

---

# 24. Dead Letter Queue Design

Invalid rows must be preserved, not discarded.

## 24.1 DLQ record should contain
- DLQ ID
- target table
- source name
- source file ID
- batch ID
- raw payload
- validation error list
- transformation stage
- row number
- failure fingerprint
- created timestamp

## 24.2 Why this matters
Messy finance files are normal.  
DLQ is a product feature, not an exception bucket.

---

# 25. Semantic Layer Design

This is what makes the system “semantic-finance-ETL” rather than just “finance-etl”.

## 25.1 Search modes

### Keyword search
Use SQLite FTS5.

### Vector search
Use `sqlite-vec`.

### Hybrid search
Blend:
- keyword scores
- vector similarity
- metadata filters

## 25.2 Embeddings
Use local `sentence-transformers`, preferably:

- `all-MiniLM-L6-v2`

## 25.3 What gets embedded
Not raw rows directly only. Better to create semantic documents such as:

- transaction narrative text
- merchant summaries
- monthly account summaries
- investment activity narratives
- rule explanations
- DLQ issue narratives if useful

## 25.4 Example narrative
A transaction row may become a semantic fragment like:

```text
On 2026-01-18, a debit card transaction of 54.23 USD was recorded for Starbucks in Seattle under Dining.
```

This is far more useful for local agent search than raw columns alone.

---

# 26. Power BI and AI-Agent Readiness

## 26.1 Power BI readiness
Design the SQLite DB with:

- clean fact tables
- clean dimensions
- consistent dates
- numeric typing
- lineage fields
- predictable keys
- indexed filter columns

## 26.2 AI-agent readiness
Design the semantic layer with:

- searchable narratives
- embeddings
- keyword index
- contextual metadata
- source provenance
- structured retrieval outputs

---

# 27. UI Architecture

You explicitly want the UI to manage configurations and trigger runs.

## 27.1 Key UI rule
The UI must **not** contain business logic.

It should call application/ETL services like:

- `ConfigRunService`
- `BatchOrchestrator`
- `SchemaService`
- `ManifestService`

## 27.2 Main UI features
The future CustomTkinter app should support:

- create/edit/delete source configs
- edit DB path and app settings
- choose discoverer type
- choose reader type
- select pipeline/target table
- edit column mappings
- preview discovered files
- run a batch
- monitor run status
- inspect DLQ rows
- view run history
- rebuild semantic indexes

## 27.3 UI architecture style
I recommend MVVM-lite:

- view: CustomTkinter windows/widgets
- viewmodel: state + UI orchestration
- services: ETL/config application services

That keeps UI maintainable.

---

# 28. Config Editing UX Strategy

Because config is the control plane, UI should make it pleasant.

## 28.1 Source wizard flow
A source creation wizard could ask:

1. choose source type
2. choose path / DB connection
3. choose discoverer strategy
4. choose reader strategy
5. choose target table pipeline
6. map columns
7. choose processing mode
8. save config
9. run preview
10. execute batch

## 28.2 Preview capabilities
UI should preview:

- discovered files
- detected columns
- sample mapped rows
- validation errors before load

This would be very powerful for personal finance onboarding.

---

# 29. Recommended Discoverer + Reader Matrix

| Scenario | Discoverer | Reader | Processing Mode |
|---|---|---|---|
| Monthly bank CSVs, same schema | `all_files` | `csv` | `raw_then_transform` |
| Bank folder, use latest statement only | `latest_modified_file` | `auto` | `single_file` |
| Broker Excel exports with changing format | `all_files` | `excel` | `transform_then_append` |
| JSON exports from app backups | `all_files` | `json` | `transform_then_append` |
| Parquet analytical dumps | `all_files` | `parquet` | `raw_then_transform` |
| Local SQLite query | `sql_dataset` | `sqlite_query` | `single_file` |
| Local PostgreSQL query | `sql_dataset` | `sql_query` | `single_file` |

---

# 30. Schema Flexibility for “Any Number of Personal Finances”

This requirement is important and should shape the system.

## 30.1 What this means architecturally
The app must support:

- multiple banks
- multiple brokers
- multiple wallets
- multiple households if desired
- multiple personal finance domains
- future custom tables

## 30.2 How to support this cleanly
Through:
- reusable config-driven sources
- reusable pipelines
- externalized mappings
- additive schema evolution
- modular table packages

## 30.3 What should remain code-based
Not everything should be config-only.

Use config for:
- source definitions
- discovery behavior
- file patterns
- mappings
- table options

Use code for:
- canonical models
- table-specific business rules
- hard validations
- key generation logic
- semantic narrative logic

That balance is important.

---

# 31. Build Strategy: What to Implement First

You asked to go step by step starting from architecture, then package structure, then core abstractions.

That is exactly right.

## Phase 1: Architecture and foundation
Build first:

- package structure
- config models
- base domain models
- contract interfaces
- SQLite connection service
- schema sync engine
- batch run tracking
- source file tracking
- DLQ table

## Phase 2: Discovery and file identity
Build next:

- `DiscoveredItem`
- discoverer contracts
- all-files discoverer
- latest-file discoverer
- file fingerprinting
- manifest service

## Phase 3: Reader infrastructure
Build:

- CSV reader
- Excel reader
- JSON reader
- Parquet reader
- SQLite reader
- auto reader

## Phase 4: Table pipeline foundation
Build:

- base pipeline class
- column mapping applier
- canonical validation flow
- loader service
- UPSERT writer

## Phase 5: First real table
Start with:

- `transactions`

Then later:

- `accounts`
- `investment_transactions`
- `holdings_snapshot`
- `market_prices`

## Phase 6: Semantic layer
Build:

- FTS5
- narrative builders
- embeddings
- sqlite-vec
- hybrid search

## Phase 7: UI
Build config editor and batch runner last, after services are stable.

---

# 32. Step-by-Step Development Plan for You

Since you want to build this carefully and not dump the whole codebase at once, this should be the order.

## Step 1: Finalize architecture decisions
Done by this design doc.

## Step 2: Freeze package structure
Create empty package directories and `__init__.py` files.

## Step 3: Build core config models
These are the true runtime backbone.

Start with:
- `AppConfig`
- `DatabaseConfig`
- `SourceConfig`
- `DiscoveryConfig`
- `ReaderConfig`
- `ProcessingConfig`

## Step 4: Build core contracts
Start with:
- `SourceDiscoverer`
- `SourceReader`
- `TablePipeline`
- `Loader`
- `Repository`
- `HashProvider`

## Step 5: Build base domain models
Start with:
- `BatchRun`
- `SourceFile`
- `DeadLetterRecord`
- `Transaction`

## Step 6: Build schema sync
Pydantic -> SQLite generation.

## Step 7: Build first discoverers
- all files
- latest modified file

## Step 8: Build first readers
- CSV
- Excel
- SQLite

## Step 9: Build first pipeline
- transactions

## Step 10: Add semantic layer
Only after core ETL is stable.

---

# 33. Assumptions

These are the assumptions I am making for the revised design:

1. You want this to be a **local desktop-grade engineering project**, not a quick script.
2. You want to onboard new sources primarily through **config + mapping**, not code edits every time.
3. You are comfortable with **YAML + Pydantic** as the config backbone.
4. You are okay with **code-based canonical models** and **config-based source definitions**.
5. SQLite is the long-term local warehouse, not a temporary staging DB.
6. Semantic search is a required feature, but not phase 1.
7. CustomTkinter UI is phase-later, not phase-1 critical path.
8. `transactions` should be the first production pipeline.

---

# 34. Architecture Decision Summary

## Final decisions

### Decision 1
Use the package architecture:

- `config`
- `domain`
- `contracts`
- `infrastructure`
- `etl`
- `tables`
- `semantic`
- `ui`

### Decision 2
Make the system **configuration-first**.

### Decision 3
Treat **source discovery as its own plugin layer**, separate from readers.

### Decision 4
Support processing modes:

- `single_file`
- `raw_then_transform`
- `transform_then_append`
- later `partitioned_batch`

### Decision 5
Use **Pydantic as the only schema source of truth**.

### Decision 6
Use **deterministic canonical IDs + record hashes** for idempotency.

### Decision 7
Build **one class-based pipeline per canonical table**.

### Decision 8
Keep UI thin; UI edits config and invokes services.

### Decision 9
Support many local source types from day one.

### Decision 10
Design for both **Power BI consumption** and **future local AI agents**.

---

# 35. My Recommendation for the Very Next Coding Step

Before writing any readers or pipelines, the **best next step** is:

## Build the configuration backbone first

Specifically in this order:

1. `config/models/database_config.py`
2. `config/models/discovery_config.py`
3. `config/models/reader_config.py`
4. `config/models/source_config.py`
5. `config/models/app_config.py`
6. `config/loader.py`

Why this first?

Because once config is right, everything else plugs into it cleanly:
- registries
- discoverers
- readers
- pipelines
- UI forms
- runner orchestration

If config is weak, the whole architecture becomes brittle.

---

# 36. Suggested “One File at a Time” Plan

When you are ready, I recommend we generate files in this exact sequence:

1. `semantic_finance_etl/config/models/database_config.py`
2. `semantic_finance_etl/config/models/discovery_config.py`
3. `semantic_finance_etl/config/models/reader_config.py`
4. `semantic_finance_etl/config/models/source_config.py`
5. `semantic_finance_etl/config/models/app_config.py`
6. `semantic_finance_etl/contracts/source_discoverer.py`
7. `semantic_finance_etl/contracts/source_reader.py`
8. `semantic_finance_etl/contracts/table_pipeline.py`
9. `semantic_finance_etl/domain/lineage/batch_run.py`
10. `semantic_finance_etl/domain/lineage/source_file.py`

That would give you a very solid foundation.

---
