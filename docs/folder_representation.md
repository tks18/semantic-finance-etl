# High-level idea

This project is best understood in 5 layers:

- **`config/`** → how the app is configured
- **`contracts/`** → interfaces / abstract definitions
- **`domain/`** → core business and runtime concepts
- **`etl/`** → orchestration and execution of pipelines
- **`infrastructure/`** → actual implementations of plugins, DB access, readers, discovery, etc.
- **`tables/`** → table-specific pipeline composition and table build logic

So in simple terms:

- **config = what the user wants**
- **contracts = what components must look like**
- **domain = what the system means**
- **etl = how the system runs**
- **infrastructure = how it physically connects and executes**
- **tables = how table pipelines are organized**

---

# Folder-by-folder summary

## `config/`
This folder contains everything related to **reading, validating, merging, and preparing configuration**.

It represents the **declarative control plane** of the app.

### It should contain
- config schemas
- config parsing
- config merging / inheritance
- defaults
- config validation helpers
- config resolution logic

### It should not contain
- business transformation logic
- source discovery implementation
- database write logic
- hook execution logic

### Mental model
`config/` answers:

> “What has the user configured this system to do?”

---

## `config/loaders/`
This subfolder contains code for **loading configuration files from disk** and turning raw YAML/JSON/TOML into Python dictionaries or validated config objects.

### It should contain
- YAML loaders
- multi-file config assemblers
- `extends` resolution
- environment variable interpolation
- config path resolution
- project config bootstrapping

### Example responsibilities
- load `project.yaml`
- load all files under `configs/tables/`
- merge parent + child config
- resolve `${ENV_VAR}` placeholders

### It should not contain
- Pydantic model definitions
- ETL orchestration logic
- runtime hook execution

### Mental model
`config/loaders/` answers:

> “How do I load config from files into memory?”

---

## `config/models/`
This contains the **typed configuration models** — usually Pydantic models.

It defines the official config structure for the application.

### It should contain
- `ProjectConfig`
- `SourceConfig`
- `TableConfig`
- `HookBindingConfig`
- `SemanticConfig`
- `RuntimeConfig`

### Example responsibilities
- define what fields a table config supports
- validate hook binding syntax
- define allowed load modes
- enforce required config structure

### It should not contain
- file reading logic
- runtime execution logic
- database connection logic

### Mental model
`config/models/` answers:

> “What does valid config look like?”

---

## `config/services/`
This contains **higher-level configuration services** that operate on already-loaded config.

Think of this as the **config intelligence layer**.

### It should contain
- config resolution services
- config normalization
- config linting
- config dependency mapping
- config-to-runtime-plan conversion

### Example responsibilities
- resolve all hook bindings for a table
- convert config into runtime execution plans
- detect duplicate table names
- validate source-to-table mappings
- build a project-wide compiled config view

### It should not contain
- raw YAML reading
- database I/O
- actual ETL step execution

### Mental model
`config/services/` answers:

> “Now that config is loaded, how do I prepare it for runtime use?”

---

## `contracts/`
This folder contains the **abstract interfaces / protocols / base contracts** that define how pluggable components behave.

This is one of the most important folders for clean architecture.

### It should contain
- `SourceDiscoverer`
- `SourceSelector`
- `SourceGrouper`
- `SourceReader`
- `Hook`
- `Loader`
- `Validator`
- `SemanticBuilder`
- plugin registry contracts

### Why it matters
This folder lets the system depend on **behavior contracts**, not concrete implementations.

For example:
- ETL orchestration depends on a `SourceReader` interface
- not specifically on a CSV reader class

### It should not contain
- concrete implementations
- file system scanning code
- SQLite-specific logic

### Mental model
`contracts/` answers:

> “What methods and behavior must each component provide?”

---

## `domain/`
This contains the **core business and runtime concepts** of the application.

It is the conceptual heart of the system.

If `contracts/` defines interfaces, `domain/` defines **meanings**.

### It should contain
- enums
- domain models
- runtime payload models
- lineage models
- schema metadata concepts
- semantic concepts
- pipeline state models

### It should not contain
- file system access
- DB-specific SQL execution
- YAML parsing
- UI code

### Mental model
`domain/` answers:

> “What concepts exist in this ETL platform?”

---

## `domain/enums/`
This folder holds system-wide enumerations and controlled vocabularies.

### It should contain
- `HookStage`
- `TableKind`
- `LoadMode`
- `SourceType`
- `ValidationSeverity`
- `ExecutionStatus`

### Why it matters
Enums make the system safer and more explicit.

Instead of random strings everywhere, you use typed known values.

### Mental model
`domain/enums/` answers:

> “What are the officially allowed values for core system concepts?”

---

## `domain/models/`
This contains the **typed runtime models** representing important objects that flow through the system.

### It should contain
- execution context
- hook payloads
- hook results
- discovered source asset models
- source group models
- runtime table definition models
- lineage event models
- DLQ row models
- schema diff models

### Example responsibilities
- represent a discovered file
- represent a batch of rows being transformed
- represent a validated load payload
- represent lineage for one hook execution

### It should not contain
- loaders for those objects
- database persistence code
- orchestration code

### Mental model
`domain/models/` answers:

> “What are the structured objects the engine thinks in?”

---

## `etl/`
This folder contains the **runtime execution layer** of the ETL engine.

This is where pipelines are actually run.

### It should contain
- orchestration logic
- execution planning
- hook stage execution
- validation pipeline
- load pipeline
- run tracking
- lineage capture
- DLQ routing

### It should not contain
- raw config file loading
- abstract contracts
- reader implementations
- filesystem discovery implementations

### Mental model
`etl/` answers:

> “How does the ETL process actually execute?”

---

## `etl/hooks/`
This contains the runtime machinery for **finding, resolving, validating, and executing hooks**.

It is the operational layer for your typed Python hook system.

### It should contain
- hook registry usage
- hook binding resolution
- hook execution runner
- hook context builder
- hook lineage recorder
- hook error handling

### Example responsibilities
- resolve `normalize_investment_transactions`
- validate its params against `params_model`
- check stage compatibility
- instantiate and execute hook
- capture row counts before and after

### It should not contain
- the actual user-defined hook scripts themselves
- raw config file loading
- source discovery implementations

### Mental model
`etl/hooks/` answers:

> “How do hooks get executed safely inside the runtime?”

---

## `etl/loading/`
This contains the logic that prepares and performs **writes into target storage**, usually SQLite here.

### It should contain
- insert/upsert planning
- merge logic
- record hash handling
- primary key handling
- load batching
- write execution coordination

### Example responsibilities
- create insert statements
- detect changed rows
- upsert canonical tables
- handle load modes like append/replace/upsert

### It should not contain
- raw DB connection setup details
- discovery logic
- hook registration logic

### Mental model
`etl/loading/` answers:

> “How do validated rows get loaded into the target store?”

---

## `etl/orchestration/`
This is the **brain** of the ETL runtime.

It coordinates discovery, reading, hooks, validation, load, derived builds, and run tracking.

### It should contain
- ETL run services
- pipeline executors
- DAG resolution
- dependency ordering
- run lifecycle management

### Example responsibilities
- run source A before derived table B
- execute all tables in dependency order
- coordinate hook stages
- manage one ETL run from start to finish

### It should not contain
- direct CSV reading code
- SQLite SQL details
- raw YAML parsing

### Mental model
`etl/orchestration/` answers:

> “In what order and under what plan does everything run?”

---

## `etl/validation/`
This folder contains logic for checking whether data is valid **after transformation and before load**.

### It should contain
- schema validation
- business-rule validation
- row-level validation
- DLQ split logic
- validation summaries

### Example responsibilities
- ensure required columns exist
- ensure dates parse correctly
- ensure quantity is non-negative if required
- split bad records into DLQ payloads

### It should not contain
- hook implementation logic
- actual DB writing
- source selection logic

### Mental model
`etl/validation/` answers:

> “Is this data safe and correct enough to load?”

---

## `infrastructure/`
This folder contains the **real-world implementations** of the abstractions in `contracts/`.

If `contracts/` says *what* a discoverer is, `infrastructure/` contains the actual filesystem discoverer.

### It should contain
- concrete plugin implementations
- database adapters
- reader implementations
- discovery implementations
- selection implementations
- grouping implementations
- filesystem utilities

### It should not contain
- core business/domain definitions
- ETL orchestration policy
- config schemas

### Mental model
`infrastructure/` answers:

> “How is this actually implemented against real technologies?”

---

## `infrastructure/database/`
This contains concrete database access logic.

### It should contain
- SQLite connection management
- SQL execution helpers
- transaction handling
- schema DDL execution
- repository/adaptor classes
- low-level DB persistence support

### Example responsibilities
- connect to SQLite
- run `CREATE TABLE`
- execute UPSERT statements
- persist lineage rows
- write DLQ entries

### It should not contain
- high-level load orchestration
- table config logic
- hook binding resolution

### Mental model
`infrastructure/database/` answers:

> “How do we physically talk to the database?”

---

## `infrastructure/discovery/`
This contains concrete implementations of **source discovery**.

### It should contain
- filesystem discoverers
- folder scanners
- pattern-based discovery
- recursive discovery
- archive discovery later if needed

### Example responsibilities
- scan folders for CSV files
- scan folders for `.sqlite` backups
- return discovered source assets with metadata

### It should not contain
- file selection policy
- file reading logic
- ETL orchestration

### Mental model
`infrastructure/discovery/` answers:

> “What source assets exist?”

---

## `infrastructure/factories/`
This folder contains **factory classes** that construct concrete objects from config or runtime context.

### It should contain
- discoverer factory
- selector factory
- grouper factory
- reader factory
- validator factory
- loader factory

### Why it matters
Instead of scattering `if/else` creation logic everywhere, factories centralize component construction.

### Example responsibilities
- if config says `discoverer: filesystem`, return `FileSystemDiscoverer`
- if reader type is `sqlite_query`, return `SQLiteQueryReader`

### It should not contain
- business transformation logic
- orchestration policy
- config model definitions

### Mental model
`infrastructure/factories/` answers:

> “Given config, which concrete implementation should I instantiate?”

---

## `infrastructure/grouping/`
This contains concrete implementations of **source grouping**.

### It should contain
- single-group grouping
- group-by-folder grouping
- group-by-date grouping
- group-by-pattern grouping

### Example responsibilities
- group all files from the same folder together
- group files by year-month
- group files matching account IDs together

### It should not contain
- discovery logic
- reader logic
- hook execution logic

### Mental model
`infrastructure/grouping/` answers:

> “How should discovered assets be batched together for processing?”

---

## `infrastructure/plugins/`
This contains the runtime support for **discovering, loading, and managing plugins**, especially user-defined hooks.

### It should contain
- plugin loader
- hook registry implementation
- module import utilities
- plugin metadata extraction
- dynamic class registration

### Example responsibilities
- import modules from `user_hooks`
- inspect classes implementing `BaseHook`
- register hook metadata
- detect duplicate hook names

### It should not contain
- hook execution runtime itself
- YAML config parsing
- DB writes

### Mental model
`infrastructure/plugins/` answers:

> “How do we find and register external pluggable components?”

---

## `infrastructure/readers/`
This contains concrete implementations of **reading data from source assets**.

### It should contain
- CSV reader
- Excel reader
- JSON reader
- Parquet reader
- SQLite table reader
- SQLite query reader
- SQL query reader

### Example responsibilities
- open file
- parse into DataFrame
- run SQL against a source DB
- return typed read payload

### It should not contain
- selection logic
- source discovery logic
- high-level ETL orchestration

### Mental model
`infrastructure/readers/` answers:

> “How do we actually extract rows from a source?”

---

## `infrastructure/selection/`
This contains concrete implementations of **which discovered assets should be chosen**.

### It should contain
- latest-modified selector
- all-files selector
- top-N selector
- filename regex selector
- changed-since-last-run selector

### Example responsibilities
- choose the latest file only
- choose only unprocessed files
- choose files inside a date range

### It should not contain
- discovery logic
- grouping logic
- file reading logic

### Mental model
`infrastructure/selection/` answers:

> “From the assets we found, which ones should actually be processed?”

---

## `tables/`
This folder is for **table-oriented pipeline composition**.

This is where the system organizes how a table gets built, transformed, validated, and loaded.

It sits between generic ETL runtime and actual configured tables.

### It should contain
- configured table pipeline logic
- derived table pipeline logic
- transform stage coordination for table pipelines
- table-specific execution helpers
- dependency-aware build flows for tables

### Example responsibilities
- run the configured ingestion pipeline for `investment_transactions`
- run derived build pipeline for `portfolio_analysis`
- coordinate table-level hooks around append/load stages
- prepare target schema for one table

### It should not contain
- raw reader implementations
- DB connection plumbing
- generic config file loading

### Mental model
`tables/` answers:

> “How is one table pipeline assembled and executed?”

---

# Very short one-line summary table

| Folder | What it represents |
|---|---|
| `config/` | configuration system and config preparation |
| `config/loaders/` | load config files from disk |
| `config/models/` | typed config schemas |
| `config/services/` | config resolution and config intelligence |
| `contracts/` | interfaces / protocols for pluggable components |
| `domain/` | core concepts and runtime meaning of the system |
| `domain/enums/` | allowed constant values / enums |
| `domain/models/` | typed runtime objects and payloads |
| `etl/` | actual ETL execution layer |
| `etl/hooks/` | hook resolution and execution machinery |
| `etl/loading/` | loading rows into target storage |
| `etl/orchestration/` | runtime coordination and pipeline control |
| `etl/validation/` | validation and DLQ routing |
| `infrastructure/` | concrete technical implementations |
| `infrastructure/database/` | database adapters and SQL execution support |
| `infrastructure/discovery/` | source discovery implementations |
| `infrastructure/factories/` | instantiate implementations from config |
| `infrastructure/grouping/` | source grouping implementations |
| `infrastructure/plugins/` | plugin and hook registration/loading |
| `infrastructure/readers/` | file/DB readers |
| `infrastructure/selection/` | source selection implementations |
| `tables/` | table-centric pipeline assembly and execution |

---

# Best mental model to remember everything

If you want one simple way to remember all this:

## `config`
**what is requested**

## `contracts`
**what shape components must follow**

## `domain`
**what the system means**

## `infrastructure`
**how real technology implements it**

## `etl`
**how it runs**

## `tables`
**how table pipelines are organized**

---

