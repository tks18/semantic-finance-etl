# `semantic-finance-ETL` v3 Design Document
## Local-first, privacy-preserving, configuration-orchestrated ETL and semantic analytics engine with strongly typed Python hook-based transformations

---

## 1. Executive Architecture Decision

`semantic-finance-ETL` should remain a **generic ETL runtime**, not a hardcoded personal finance app.

However, the transformation model should be revised:

### Final design decision
- **configuration defines orchestration**
- **Python hook scripts define processing**
- **source discovery, selection, grouping, lineage, schema compilation, and loading remain first-class engine features**
- **UI, domain layer, and overall package structure remain intact**
- **configuration should feel declarative and ergonomic, not like writing a second programming language**

So the correct mental model becomes:

```text
semantic-finance-ETL
=
config-orchestrated ETL engine
+
strongly typed Python hook runtime
+
dynamic schema/compiler system
+
source discovery framework
+
semantic indexing layer
```

Not:

```text
app config = place where all logic is painfully encoded
```

And not:

```text
every transformation must be expressed in a declarative mini-DSL
```

Instead:

```text
config says what to run
Python hooks say how to transform
engine guarantees safety, ordering, lineage, idempotency, validation, and load behavior
```

---

## 2. What Stays the Same vs What Changes

## 2.1 What stays the same
The following parts of the previous design remain correct and should be preserved:

- **local-first architecture**
- **plugin-based source discovery**
- **SourceDiscoverer / SourceSelector / SourceGrouper / SourceReader separation**
- **dynamic runtime-generated tables**
- **Pydantic as schema and validation authority**
- **SQLite as the local analytics store**
- **semantic document generation + FTS5 + vector search**
- **UI as config editor + execution console**
- **derived tables as first-class DAG nodes**
- **lineage, DLQ, idempotency, and run tracking as core features**
- **top-level package structure**
- **domain-oriented layering**

---

## 2.2 What changes
The main change is in the transformation engine.

### Old direction
The prior document leaned toward:
- config-defined transform steps
- a transform DSL
- declarative joins/group-bys/windows in config

### New direction
Your revised requirement is better:

- **all transformations on tables happen in Python scripts/hooks**
- config should only declare:
  - when a hook runs
  - where it runs
  - on which source/table it runs
  - with what typed parameters
- hooks must be:
  - **fully typed**
  - **stage-aware**
  - **safe to validate**
  - **strongly bound to runtime schema expectations**

This is a cleaner and more scalable design.

---

## 3. Revised Core Philosophy

The engine should own the **platform concerns**.

Python hooks should own the **business/data transformation concerns**.

### Engine responsibilities
The engine should know **how to**:

1. load config
2. discover sources
3. select sources
4. group sources
5. read files / query DBs
6. compile runtime schema models
7. invoke hooks at the right lifecycle stage
8. validate results
9. append / merge / upsert into SQLite
10. record lineage
11. manage DLQ
12. build semantic projections
13. run derived-table dependencies
14. expose Power BI / local agent friendly tables

### Hook responsibilities
Hooks should know **how to**:

1. clean raw extracted data
2. reshape source-specific datasets
3. derive business fields
4. normalize weird layouts
5. enrich records
6. combine batches intelligently
7. perform final pre-load shaping
8. compute derived analytical tables
9. optionally influence semantic projection preparation

This is the correct separation of concerns.

---

## 4. Revised Architectural Style

Use the same layered architecture, but make **hook orchestration** a first-class subsystem.

```text
UI / CLI Layer
    ↓
Application Services / ETL Orchestration
    ↓
Domain Models + Hook Contracts + Runtime Schemas
    ↓
Infrastructure Implementations

Cross-cutting:
Config, Plugin Registry, Hook Registry, Logging, Lineage, Run Tracking, Schema Compilation
```

---

## 5. Top-Level Layers

These top-level layers remain the same:

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

### Important note
We are **not changing the shape of the application**.

We are changing **how transformations are expressed and executed**.

---

## 6. New High-Level Processing Model

The runtime should process a project like this:

```text
ProjectConfig
  ├── SourceDefinitions
  ├── TableDefinitions
  ├── HookBindings
  ├── DerivedTableDefinitions
  ├── SemanticDefinitions
  └── RuntimeSettings

Discovery
  ↓
Selection
  ↓
Grouping
  ↓
Reading
  ↓
Hook execution at lifecycle stages
  ↓
Validation
  ↓
Load / append / upsert
  ↓
Derived-table builds
  ↓
Semantic projection
  ↓
FTS5 + vector indexing
```

---

## 7. Most Important New Design Decision: Hook-Centric Transformation Model

## 7.1 Why this is the right move
Your instinct is correct: if transformation logic becomes too config-heavy, the config turns into:

- a DSL nobody likes
- a debugging nightmare
- an unreadable pseudo-program
- a painful UI burden

By moving real transformation logic into Python scripts, you get:

- normal programming power
- reuse across tables and projects
- testability
- IDE help
- mypy / pyright support
- easier debugging
- better performance tuning
- more natural handling of edge cases

### So config should not describe transformations in detail
Config should describe:

- **which hook**
- **at which stage**
- **in what order**
- **with what parameters**
- **under what execution policy**

That is the right level of abstraction.

---

## 7.2 Final rule
### All data/table transformations should happen through Python hooks
That includes:

- row cleanup
- column normalization
- enrichment
- joins
- aggregations
- post-read cleanup
- pre-load shaping
- derived table calculations
- semantic-preparation shaping

Config should **reference** hooks, not try to replace them.

---

# 8. Hook System Design

## 8.1 Hook categories
The hook model should be explicit and stable.

### Hook categories
1. `RunHook`
2. `DiscoveryHook`
3. `SelectionHook`
4. `GroupingHook`
5. `ReadHook`
6. `AppendHook`
7. `ValidationHook`
8. `LoadHook`
9. `DerivedTableHook`
10. `SemanticHook`

Not every project will use all of them, but the system should support them.

---

## 8.2 Hook scopes
A hook can operate at one of several scopes:

| Scope | Purpose |
|---|---|
| `project` | project-wide behavior |
| `source` | acts on one source definition |
| `source_group` | acts on grouped source assets |
| `table` | acts on one table pipeline |
| `derived_table` | acts on analytical DAG nodes |
| `semantic_projection` | shapes semantic docs/chunks |
| `run` | global run-start / run-end logic |

This matters because the same lifecycle stage can mean different things at different scopes.

---

## 8.3 Lifecycle stages
The engine should expose well-defined hook points.

### Recommended hook stages
- `on_run_start`
- `pre_discovery`
- `post_discovery`
- `pre_selection`
- `post_selection`
- `pre_grouping`
- `post_grouping`
- `pre_read`
- `post_read`
- `pre_append`
- `post_append`
- `pre_validate`
- `post_validate`
- `pre_load`
- `post_load`
- `pre_derive`
- `post_derive`
- `pre_semantic`
- `post_semantic`
- `on_run_end`
- `on_error`

These stages directly support the behavior you asked for:

- **pre-appending**
- **post-appending**
- **pre-posting to DB**
- plus everything around them

---

## 8.4 The key stages for your use case
If we simplify to the most important ones, the core table pipeline becomes:

```text
read source
  ↓
post_read hook(s)
  ↓
pre_append hook(s)
  ↓
append / combine
  ↓
post_append hook(s)
  ↓
pre_validate hook(s)
  ↓
validation
  ↓
pre_load hook(s)
  ↓
load into SQLite
  ↓
post_load hook(s)
```

This is exactly the architecture you were pointing toward.

---

## 8.5 Hook execution order
Hook ordering must be deterministic.

### Rule
Within a stage, hooks run in:

1. explicit `order`
2. then `priority`
3. then `hook_id`

This ensures reproducible output.

### Recommended precedence
- project-level hooks
- source-level hooks
- table-level hooks
- load-level hooks

But stage-specific overrides should be allowed where sensible.

---

## 8.6 Hook execution policy
Each hook binding should support policies like:

- `enabled: true/false`
- `fail_behavior: fail_run | skip_hook | route_to_dlq | warn_only`
- `timeout_seconds`
- `retry_count`
- `execution_mode: per_file | per_group | per_table | per_partition`
- `run_if_source_changed_only`
- `run_if_dependencies_changed_only`

This keeps the system safe and operationally predictable.

---

# 9. Strongly Typed Hook Contract Design

## 9.1 Non-negotiable requirement
Hooks must be **fully typed and strong**.

That means a hook should not just be:

```python
def run(df):
    ...
```

That is too weak.

Instead, each hook should declare:

- its stage
- its input payload type
- its output payload type
- its parameter schema
- optionally supported table kinds / source kinds
- metadata about whether it mutates schema, columns, or row cardinality

---

## 9.2 Recommended contract pattern
Use a generic contract pattern like:

```python
class Hook(Protocol[InputT, OutputT, ParamsT]):
    hook_name: ClassVar[str]
    stage: ClassVar[HookStage]
    params_model: ClassVar[type[ParamsT]]

    def execute(
        self,
        context: ExecutionContext,
        payload: InputT,
        params: ParamsT,
    ) -> OutputT:
        ...
```

This gives strong typing at the contract layer.

---

## 9.3 Stage-specific typed payloads
Instead of one generic payload, define explicit payload models.

### Examples
- `DiscoveryPayload`
- `ReadPayload`
- `BatchPayload`
- `ValidatedBatchPayload`
- `LoadPayload`
- `DerivedBuildPayload`
- `SemanticProjectionPayload`

Each should be a Pydantic model or typed domain object.

---

## 9.4 Example payload responsibilities

| Payload | Contains |
|---|---|
| `DiscoveryPayload` | discovered assets, source config, execution metadata |
| `ReadPayload` | source asset, raw frame, inferred schema, parse metadata |
| `BatchPayload` | list of frames/assets, combine strategy, lineage refs |
| `ValidatedBatchPayload` | validated rows/frame, validation summary, target schema |
| `LoadPayload` | rows/frame to be loaded, load plan, PK strategy, record hash plan |
| `DerivedBuildPayload` | dependent tables, materialization target, valuation date/run metadata |
| `SemanticProjectionPayload` | table rows, templates, chunk config, semantic metadata |

This is how the hook system becomes strong rather than loose.

---

## 9.5 Hook parameter typing
Every hook should define a dedicated Pydantic parameter model.

Example:

```python
class NormalizeBrokerTradesParams(BaseModel):
    account_name_from_filename: bool = True
    drop_zero_quantity: bool = True
    allowed_trade_types: list[str] = ["BUY", "SELL", "DIVIDEND"]
```

This gives:

- config validation
- UI form generation
- defaults
- auto-documentation
- safe evolution

This is one of the biggest reasons config can feel pleasant instead of painful.

---

## 9.6 Hook result typing
Hook outputs should not be raw DataFrames alone.

Return a structured result such as:

- updated frame/payload
- mutation metadata
- warnings
- schema impact summary
- lineage annotations
- metrics

Example result fields:

- `rows_in`
- `rows_out`
- `columns_added`
- `columns_removed`
- `schema_changed`
- `warnings`
- `timing_ms`

This makes hooks observable and debuggable.

---

## 9.7 Schema-safety contracts
Each hook should declare whether it:

- preserves schema
- adds columns
- removes columns
- renames columns
- changes row count
- expects certain input columns
- guarantees certain output columns

This is essential because the system is dynamic.

Without this, Python hooks become too magical.

---

# 10. Configuration Should Feel Like a Great Thing, Not a Pain Point

This is one of the most important product decisions.

## 10.1 Config should express intent, not implementation
Good config says:

- use source X
- pick latest modified file
- read via SQLite query reader
- apply hook A after read
- apply hook B before load
- load into table Y

Bad config says:

- here is a 300-line nested pseudo-language with every transformation spelled out awkwardly

So the rule is:

### config is orchestration metadata, not a substitute for Python

---

## 10.2 Ergonomic config principles
To make config pleasant, the system should enforce these rules:

1. **sane defaults everywhere**
2. **small number of required fields**
3. **hook params with defaults**
4. **reusable source templates**
5. **reusable hook bindings**
6. **UI-assisted config generation**
7. **preview before save**
8. **config linting**
9. **config inheritance / profiles**
10. **clear runtime error messages tied to config paths**

---

## 10.3 Keep the config layout mostly unchanged
Keep the layout from the earlier roadmap:

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

### Important refinement
Do **not** add a giant separate transformation DSL file unless absolutely necessary.

Instead, embed hook bindings in:

- source configs
- table configs
- derived table configs

That keeps config structure stable and intuitive.

---

## 10.4 Recommended config concepts
Every project config should include:

- project metadata
- local DB path
- plugin/hook search paths
- source definitions
- selector definitions
- reader definitions
- table definitions
- hook bindings
- semantic definitions
- idempotency settings
- indexing settings
- execution settings

---

## 10.5 Example: source config with discovery + hook stages

```yaml
source_id: broker_sqlite_backups
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

target_tables: ["investment_transactions"]

hooks:
  post_read:
    - hook: normalize_broker_trades
      order: 10
      params:
        account_name_from_filename: false
        drop_zero_quantity: true

  pre_append:
    - hook: standardize_trade_schema
      order: 20

  post_append:
    - hook: deduplicate_broker_rows
      order: 30

  pre_load:
    - hook: assign_canonical_ids
      order: 40
```

This is very readable and does not feel like a pain point.

---

## 10.6 Example: table config with strong schema + hooks

```yaml
table_name: investment_transactions
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

hooks:
  pre_validate:
    - hook: enforce_trade_business_rules
      order: 10
  pre_load:
    - hook: enrich_trade_tags
      order: 20

load:
  mode: upsert
  record_hash: true
```

Again, this is orchestration config, not transformation programming.

---

## 10.7 Config inheritance and presets
To make configuration delightful, support:

- `extends`
- `defaults`
- `profiles`
- `presets`
- environment-variable interpolation
- reusable hook param presets

Example uses:

- many bank CSVs share the same selector
- many broker files share the same post-read normalizer
- many derived tables share the same materialization defaults

This dramatically reduces repetition.

---

## 10.8 UI-generated config forms
Because hook params are typed, the UI can automatically generate forms from each hook’s Pydantic model.

That means the user experience becomes:

- choose hook from registry
- UI shows parameter form
- defaults pre-filled
- validation happens immediately
- tooltips come from field descriptions
- save only valid config

This is exactly how configuration becomes a strength.

---

# 11. Source Discovery Must Remain First-Class

You explicitly said this is key, and I agree completely.

## 11.1 Discovery architecture should remain unchanged
The prior separation is still correct:

- `SourceDiscoverer`
- `SourceSelector`
- `SourceGrouper`
- `SourceReader`

This architecture should remain independent of hooks.

Hooks can enhance discovery stages, but they should **not replace discovery architecture**.

---

## 11.2 Why this separation is still essential
Because these are different decisions:

- **what exists?** → discovery
- **which ones should run?** → selection
- **how are they batched?** → grouping
- **how do we read them?** → reading
- **when do we transform?** → hook stages

If you collapse them into a single mechanism, extensibility degrades quickly.

---

## 11.3 Supported selector plugins
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

These remain extremely valuable.

---

## 11.4 Supported grouping plugins
At minimum:

- `single_group`
- `group_by_parent_folder`
- `group_by_filename_pattern`
- `group_by_date_partition`
- `group_by_source_type`

---

## 11.5 Supported readers
At minimum:

- `csv_reader`
- `excel_reader`
- `parquet_reader`
- `json_reader`
- `sqlite_table_reader`
- `sqlite_query_reader`
- `sql_query_reader`
- `duckdb_reader`

And later:

- XML
- fixed-width
- Access export
- zipped archive readers

---

# 12. Revised Combine Strategy Model

Because transformations are now hook-driven, combine behavior must be hook-aware.

## 12.1 Recommended combine strategies
Support these modes:

| Strategy | Meaning | Best use case |
|---|---|---|
| `single_file_only` | process one selected asset only | latest report |
| `hook_each_then_append` | run per-file hooks first, then union | messy files |
| `append_then_hook` | union first, then run batch-level hook | stable repeated extracts |
| `query_each_then_union` | query multiple DBs, then union | SQLite backup folders |
| `partition_then_hook` | split by partition, hook process each | large datasets |

### My recommendation
- default to **`hook_each_then_append`**
- use **`append_then_hook`** only when schemas are already aligned
- use **`query_each_then_union`** for folder-based DB discovery

---

## 12.2 Where your requested hook points fit
You mentioned:

- pre-appending
- post-appending
- pre-posting to DB

These fit exactly like this:

| Stage | Purpose |
|---|---|
| `post_read` | clean each extracted dataset |
| `pre_append` | make each dataset append-compatible |
| `post_append` | run combined normalization/dedup/consolidation |
| `pre_load` | final shaping before SQLite write |
| `post_load` | post-write side effects or metadata updates |

This is a clean and powerful lifecycle.

---

# 13. Dynamic Tables and Runtime Schema Strategy

## 13.1 Pydantic remains the schema authority
That should not change.

Use this pipeline:

```text
Config → RuntimeTableDefinition → Runtime Pydantic Model → SQLite DDL → Validation
```

So Pydantic is still the source of truth, but generated dynamically.

---

## 13.2 Static vs dynamic models

### Static code-defined models
Use normal models for:

- `etl_runs`
- `source_files`
- `lineage_events`
- `dead_letter_queue`
- `schema_registry`
- `semantic_documents`
- `semantic_embeddings`
- `config_snapshots`

### Runtime-generated models
Use dynamic models for:

- user-defined ingestion tables
- canonical normalized tables
- derived analytical tables
- project-specific tables

---

## 13.3 Hook compatibility with dynamic schemas
Since tables are dynamic, hooks must declare compatibility in a structured way.

A hook should be able to specify:

- supported table names
- supported table kinds
- required columns
- optional columns
- produced columns
- whether schema mutation is expected

This allows the engine to validate bindings at startup.

---

## 13.4 Schema evolution rules
### Safe automatic changes
- add nullable column
- add defaulted column
- widen text-like column
- add semantic metadata column

### Controlled changes
- incompatible type change
- column removal
- column rename
- primary key strategy change
- output schema changes from a hook that violate expected table definition

If a hook introduces a schema drift, the engine should catch it before load.

---

# 14. Analytical / Derived Tables Remain First-Class

## 14.1 Derived tables should stay as DAG nodes
This is still correct.

The difference is that their build logic is now usually hook-based.

### Example
`portfolio_analysis` depends on:

- `investment_transactions`
- `market_prices`
- `benchmark_master`
- `benchmark_prices`

But instead of a large config DSL, it can use:

- dependency config
- materialization config
- one or more Python derived-table hooks

That is cleaner.

---

## 14.2 Derived table config pattern

```yaml
table_name: portfolio_analysis
table_kind: derived

depends_on:
  - investment_transactions
  - market_prices
  - benchmark_master
  - benchmark_prices

build:
  strategy: python_hook
  hooks:
    - hook: build_portfolio_analysis
      order: 10
      params:
        benchmark_default: NIFTY_50
        compute_xirr: true
        compute_cagr: true

materialization:
  type: table
  rebuild_on_dependency_change: true
```

This is much more maintainable than a huge nested transform language.

---

## 14.3 Materialization modes
Keep support for:

- `table`
- `view`
- `incremental_table`
- `ephemeral`

### Recommendation
- use `table` for Power BI
- use `view` for light reusable projections
- use `incremental_table` only after the engine is stable

---

# 15. Python Hooks Should Still Map Cleanly to SQL-Like Thinking

Even though transformations move to Python, the mental model should remain analytically rigorous.

## 15.1 Why this matters
Finance and analytics users still think in operations like:

- `JOIN`
- `GROUP BY`
- `WINDOW`
- `FILTER`
- `UNION`

So Python hook code should be written in a way that clearly corresponds to these concepts.

---

## 15.2 Example: join operation in a hook

Conceptually, if a hook enriches transactions with prices, it is performing a `LEFT JOIN`.

### SQL mental model

```sql
SELECT
    t.*,
    p.close_price
FROM investment_transactions t
LEFT JOIN market_prices p
    ON t.symbol = p.symbol
   AND t.valuation_date = p.valuation_date;
```

### Hook mental model
The Python hook should express the same logic using Polars or pandas, but in a typed, testable function.

---

## 15.3 Example: group-by aggregation in a hook

### SQL mental model

```sql
SELECT
    portfolio_id,
    SUM(cost_basis) AS total_cost,
    SUM(market_value) AS total_value
FROM portfolio_positions
GROUP BY portfolio_id;
```

### Hook mental model
The derived-table hook computes the same result using DataFrame operations, but the engine still understands:

- dependencies
- lineage
- target schema
- load behavior

---

## 15.4 Example: window logic in a hook

### SQL mental model

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

### Design decision
Even though implementation is in Python, the architecture should document such hooks as performing:

- join
- group-by
- window-style calculations

This keeps the system analytically transparent.

---

# 16. Validation, Load, DLQ, and Idempotency

## 16.1 Validation flow
Validation should happen after relevant transformation hooks and before load.

Recommended sequence:

```text
read
→ transform hooks
→ schema-aware validation
→ DLQ split
→ pre_load hook
→ load
```

### Important nuance
Some hooks may intentionally coerce bad source data into valid shape.

So `pre_validate` hooks are extremely useful.

---

## 16.2 Pre-load hook is essential
You specifically asked for “pre-posting to DB” behavior.

This should be a first-class stage.

Typical `pre_load` responsibilities:

- assign canonical IDs
- compute record hashes
- normalize load-ready datatypes
- trim final columns
- apply final business rules
- attach audit metadata

This is one of the most important hook points.

---

## 16.3 DLQ remains non-negotiable
Every failed record should persist with:

- run ID
- source ID
- file path
- row number / row identifier
- raw payload
- failing hook or validation stage
- error message / validation detail
- timestamp

In the hook-based world, DLQ becomes even more important.

---

## 16.4 Idempotency layers
Keep these exactly as core engine features:

### File-level
Track:
- file path
- size
- modified timestamp
- created timestamp if available
- content hash

### Group-level
Track:
- source group hash
- selected asset set hash
- hook binding hash

### Row-level
Track:
- `canonical_id`
- `record_hash`

### Load-level
Use:
- insert if new
- update if changed
- skip if identical

---

# 17. Lineage Must Expand to Include Hook Invocations

Because transformation logic is now in Python, lineage must become more detailed.

## 17.1 Minimum lineage questions the system must answer
- which file produced this row?
- which source selector selected it?
- which hook transformed it after read?
- which hook touched it before append?
- which hook touched it before load?
- which config version was used?
- which semantic document came from it?
- which derived-table build produced this analytical row?

---

## 17.2 New hook lineage fields
Every hook invocation should record:

- `run_id`
- `table_name`
- `source_id`
- `hook_id`
- `plugin_path`
- `stage`
- `params_hash`
- `input_row_count`
- `output_row_count`
- `input_schema_hash`
- `output_schema_hash`
- `start_time`
- `end_time`
- `status`
- `error_summary`

This is critical for trust and debugging.

---

## 17.3 Why this is especially important now
When logic lives in Python, debugging is only pleasant if you can answer:

- what ran?
- in what order?
- with what parameters?
- what changed?

Without hook lineage, Python-based flexibility becomes risky.

With hook lineage, it becomes enterprise-grade.

---

# 18. Semantic Layer Remains Config-Driven

## 18.1 Data transformation vs narrative transformation
Your “Python only for transformations” requirement should apply to **data processing logic**.

The semantic layer can still remain largely config/template-driven because it is:

- presentation logic
- indexing metadata
- search shaping

That is a different concern.

---

## 18.2 Semantic pipeline remains
Keep the same flow:

```text
table rows
  → semantic projection build
  → chunking
  → FTS5 document
  → embedding vector
  → hybrid retrieval
```

---

## 18.3 Semantic hooks
In addition to templates, allow optional hook points:

- `pre_semantic`
- `post_semantic`

Use cases:
- custom text cleanup
- grouped narrative generation
- tag enrichment
- row-to-document consolidation

This gives power without making semantic config bloated.

---

# 19. UI Architecture Should Stay the Same, but Gain Hook Awareness

## 19.1 UI principle remains unchanged
The UI must not contain business logic.

It should only:

- edit config
- validate config
- preview source discovery
- preview hook bindings
- preview hook outputs
- run ETL
- inspect runs
- inspect DLQ
- inspect lineage
- trigger semantic rebuild

---

## 19.2 UI modules to keep
Keep the earlier set:

- Project selector
- Source config editor
- Table schema editor
- Semantic template editor
- Execution dashboard
- Run history
- DLQ browser
- Search tester

---

## 19.3 New UI modules to add
Add hook-specific views without changing the overall UI architecture:

- Hook registry browser
- Hook binding editor
- Hook parameter form generator
- Stage-wise data preview
- Hook execution trace viewer
- Hook test-run sandbox

This preserves the UI shape while aligning it to the new engine.

---

## 19.4 Why this matters for config experience
If users can:

- pick a hook from a registry
- see its typed parameters
- preview before/after rows
- get immediate validation

then configuration becomes a great experience rather than a pain point.

That is exactly the outcome you want.

---

# 20. Recommended Package Structure
## Keep the same top-level shape, add hook-specific internals

```text
semantic_finance_etl/
├── config/
│   ├── models/
│   │   ├── project_config.py
│   │   ├── source_config.py
│   │   ├── table_config.py
│   │   ├── transform_config.py        # now stores hook binding models
│   │   ├── semantic_config.py
│   │   └── runtime_config.py
│   ├── loaders/
│   └── services/
│
├── domain/
│   ├── enums/
│   │   └── hook_stage.py
│   ├── models/
│   │   ├── runtime_table_definition.py
│   │   ├── hook_payloads.py
│   │   ├── hook_results.py
│   │   ├── lineage_models.py
│   │   └── semantic_models.py
│   ├── schema/
│   └── metadata/
│
├── contracts/
│   ├── source_discoverer.py
│   ├── source_selector.py
│   ├── source_grouper.py
│   ├── source_reader.py
│   ├── hook.py
│   ├── validator.py
│   ├── loader.py
│   ├── semantic_builder.py
│   ├── embedding_provider.py
│   └── plugin_registry.py
│
├── infrastructure/
│   ├── discovery/
│   ├── selection/
│   ├── grouping/
│   ├── readers/
│   ├── database/
│   ├── plugins/
│   │   ├── local_plugin_registry.py
│   │   ├── hook_loader.py
│   │   └── plugin_loader.py
│   └── logging/
│
├── etl/
│   ├── orchestration/
│   │   ├── run_etl_service.py
│   │   ├── pipeline_executor.py
│   │   ├── dag_builder.py
│   │   └── dependency_resolver.py
│   ├── hooks/
│   │   ├── hook_runner.py
│   │   ├── hook_binding_resolver.py
│   │   ├── hook_context_factory.py
│   │   └── hook_lineage_recorder.py
│   ├── runtime/
│   ├── validation/
│   ├── loading/
│   ├── lineage/
│   ├── dlq/
│   └── tracking/
│
├── tables/
│   ├── configured_table_pipeline.py
│   ├── derived_table_pipeline.py
│   ├── transform_engine.py           # now coordinates hook stages
│   ├── step_factory.py               # can be repurposed or deprecated
│   └── custom/
│
├── semantic/
│   ├── narrative/
│   ├── embeddings/
│   ├── indexing/
│   └── chunking/
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

# 21. Recommended Hook Registry Design

## 21.1 Hook registry should be explicit
The system should maintain a registry of available hooks with metadata such as:

- hook ID
- plugin path
- supported stage
- supported scopes
- parameter model
- version
- docstring/description
- schema mutation policy

This enables:

- UI discovery
- config validation
- runtime compatibility checks

---

## 21.2 Hook discovery strategy
Support both:

### Built-in hooks
Shipped with the engine for common use cases.

### User hooks
Project-specific Python scripts loaded from configured search paths, for example:

- `./user_hooks/`
- `./plugins/`
- installed package modules

This allows customization without changing the engine core.

---

# 22. Example of a Typed Hook

Here is the kind of structure a real hook should follow:

```python
class NormalizeBrokerTradesParams(BaseModel):
    account_name_from_filename: bool = True
    drop_zero_quantity: bool = True

class NormalizeBrokerTradesHook(PostReadHook):
    hook_name = "normalize_broker_trades"
    params_model = NormalizeBrokerTradesParams

    def execute(
        self,
        context: ExecutionContext,
        payload: ReadPayload,
        params: NormalizeBrokerTradesParams,
    ) -> ReadPayload:
        df = payload.frame
        # normalize/cast/clean using Polars or pandas
        return payload.with_frame(df)
```

Even in this simple example, note the strengths:

- typed params
- typed input
- typed output
- stage-specific contract
- not just a raw ad hoc function

That is the right direction.

---

# 23. Testing Strategy for the Hook-Based Model

## 23.1 Hook contract tests
Every hook should be testable in isolation.

Test categories:

- parameter model validation
- required-column validation
- schema preservation or mutation expectations
- row-count behavior
- deterministic output
- failure mapping

---

## 23.2 Integration tests
Need end-to-end tests for:

- source discovery
- selection
- reading
- hook chain execution
- validation
- load
- lineage
- semantic indexing

---

## 23.3 Golden dataset tests
For important finance/analytical pipelines, keep fixture datasets and expected outputs so you can detect regressions when a hook changes.

This is especially important for:

- portfolio analysis
- cash flow series
- realized/unrealized gains
- benchmark comparison
- XIRR/CAGR calculations

---

# 24. Phase-by-Phase Implementation Plan

## Phase 1 — Preserve structure, update config models
### Goal
Keep the current architecture shape and introduce hook-aware config.

### Deliverables
- `HookStage` enum
- `HookBindingConfig`
- hook param reference model
- updated source/table config models
- config validation rules

### Acceptance criteria
- source/table configs can bind hooks at valid stages
- invalid stage-hook combinations fail validation
- config can be loaded and rendered as an execution plan

---

## Phase 2 — Hook contracts and registry
### Goal
Build the strong type-safe hook foundation.

### Deliverables
- base hook protocols
- typed payload models
- typed hook result models
- hook registry
- built-in hook metadata model

### Acceptance criteria
- hooks can be registered and discovered
- param models validate correctly
- registry exposes enough info for UI generation

---

## Phase 3 — Discovery, selection, grouping, reading
### Goal
Preserve and harden the source framework.

### Deliverables
- filesystem discoverer
- latest/all selectors
- grouping plugins
- CSV/Excel/SQLite/query readers

### Acceptance criteria
- source discovery works independently of transformation logic
- selected assets are deterministic
- folder-of-SQLite-backups case works cleanly

---

## Phase 4 — Runtime schema compiler
### Goal
Generate runtime models and SQLite DDL from config.

### Deliverables
- runtime table definitions
- dynamic Pydantic model factory
- SQLite schema compiler
- schema diff engine

### Acceptance criteria
- new table config creates SQLite table
- safe schema changes can be applied
- hooks are checked against table schema expectations

---

## Phase 5 — Hook runner and stage orchestration
### Goal
Make hook execution the heart of the transformation system.

### Deliverables
- hook runner
- hook context factory
- stage resolver
- hook lineage recorder
- error-routing behavior

### Acceptance criteria
- post-read / pre-append / post-append / pre-load hooks all run correctly
- ordering is deterministic
- hook failures respect configured fail behavior

---

## Phase 6 — Validation, load, DLQ, idempotency
### Goal
Make the pipeline safe and trustworthy.

### Deliverables
- validation service
- DLQ persistence
- load planner
- UPSERT service
- file/group/row idempotency trackers

### Acceptance criteria
- invalid records go to DLQ
- unchanged records skip correctly
- changed records update correctly
- hook lineage survives reruns

---

## Phase 7 — Derived table hooks
### Goal
Enable analytical tables using dependency-aware Python builders.

### Deliverables
- DAG builder
- dependency resolver
- derived table pipeline
- derived build hooks
- materialization manager

### Acceptance criteria
- derived tables can depend on base tables
- portfolio analysis build works
- rebuild-on-dependency-change works

---

## Phase 8 — Semantic layer and hook integration
### Goal
Retain semantic power without bloating config.

### Deliverables
- semantic template renderer
- semantic projection service
- optional semantic hooks
- FTS5 indexing
- vector indexing

### Acceptance criteria
- rows become semantic docs
- semantic rebuilds work on config/template changes
- hybrid retrieval works

---

## Phase 9 — UI enhancements
### Goal
Keep the UI architecture but make it hook-aware.

### Deliverables
- hook registry browser
- hook parameter forms
- hook binding editor
- preview before/after panels
- hook execution trace view

### Acceptance criteria
- users can bind hooks without editing raw YAML for common tasks
- typed hook params are editable in UI
- preview explains stage outputs clearly

---

## Phase 10 — Hardening
### Goal
Make the app production-style and maintainable.

### Deliverables
- structured logging
- contract test suite
- fixture library
- performance profiling
- documentation
- sample starter projects

### Acceptance criteria
- repeatable runs
- stable hook contracts
- Power BI-ready data outputs
- good developer experience for new hooks

---

# 25. Final Architecture Decision

## The correct final shape is:

### Engine
A **generic local ETL runtime**

### Behavior
**Config-orchestrated**, **hook-executed**, **typed**, **schema-aware**, **lineage-rich**, **idempotent**

### Source model
Separate first-class abstractions for:

- discovery
- selection
- grouping
- reading

### Transformation model
All real data processing logic happens through:

- **strongly typed Python hooks**
- invoked at lifecycle stages like:
  - `post_read`
  - `pre_append`
  - `post_append`
  - `pre_load`
  - `pre_derive`
  - `pre_semantic`

### Data model
Combination of:

- fixed system tables
- runtime-generated dynamic tables
- derived analytical tables
- semantic projection/index tables

### Platform stack
- local-first
- SQLite target
- Pydantic schema authority
- Polars-first data processing
- FTS5 + vector search for retrieval

---

# 26. My Strong Recommendations

## Do this
- keep source discovery architecture exactly as a first-class subsystem
- keep UI and top-level structure intact
- move all table/data transformations to typed Python hooks
- let config bind hooks, not encode logic
- make hook params Pydantic-based
- record lineage for every hook invocation
- make `pre_load` a first-class lifecycle stage
- use derived-table hooks for advanced analytics
- use UI-generated forms from hook param schemas

## Do not do this
- do not turn config into a giant transform DSL
- do not collapse discovery/selection/grouping/reading into one class
- do not let hooks be untyped loose functions
- do not allow silent schema mutations
- do not skip hook lineage and observability
- do not put transformation logic into the UI

---

# 27. Best Next Step

The best next step is now very clear:

## Step 1
Refactor the config and contract foundation to support:

- `HookStage`
- `HookBindingConfig`
- typed payload contracts
- hook registry metadata
- source/table hook attachments

### Concretely, the first files to define should be:
- `config/models/transform_config.py`  
  repurposed to hold hook-binding models
- `domain/enums/hook_stage.py`
- `domain/models/hook_payloads.py`
- `contracts/hook.py`
- `etl/hooks/hook_runner.py`

That would lock in the architecture correctly before any reader or UI implementation goes too far.

---

# 28. Hooks Linking Strategy - Example

The cleanest way is **not** to hardcode the Python file path inside every table config.

Instead, use a **2-level linking model**:

1. **project/runtime config** tells the app **where hook files live**
2. **table config** references the hook by a **stable hook name / id**

That way:

- your `investment_transformations.py` can contain many hooks
- table configs stay readable
- refactoring files later does not break all YAMLs
- the UI can show a friendly hook registry
- params can be validated strongly from the hook’s typed param model

---

## Recommended linking pattern

## 1) Put your hook file in a known hooks folder

Example:

```text
semantic_finance_etl/
├── user_hooks/
│   ├── __init__.py
│   └── investment_transformations.py
├── configs/
│   ├── project.yaml
│   └── tables/
│       └── investment_transactions.yaml
```

---

## 2) Define the hook class with a stable `hook_name`

Example `user_hooks/investment_transformations.py`:

```python
from __future__ import annotations

from decimal import Decimal
from typing import ClassVar

from pydantic import BaseModel, Field
import polars as pl

from semantic_finance_etl.contracts.hook import TableHook
from semantic_finance_etl.domain.enums.hook_stage import HookStage
from semantic_finance_etl.domain.models.hook_payloads import BatchPayload
from semantic_finance_etl.domain.models.execution_context import ExecutionContext


class NormalizeInvestmentTransactionsParams(BaseModel):
    drop_zero_quantity: bool = Field(default=True)
    uppercase_symbol: bool = Field(default=True)
    trim_account_name: bool = Field(default=True)
    allowed_transaction_types: list[str] = Field(
        default_factory=lambda: ["BUY", "SELL", "DIVIDEND", "BONUS"]
    )


class NormalizeInvestmentTransactionsHook(
    TableHook[BatchPayload, BatchPayload, NormalizeInvestmentTransactionsParams]
):
    hook_name: ClassVar[str] = "normalize_investment_transactions"
    stage: ClassVar[HookStage] = HookStage.POST_APPEND
    params_model = NormalizeInvestmentTransactionsParams

    required_columns: ClassVar[set[str]] = {
        "trade_date",
        "symbol",
        "transaction_type",
        "quantity",
        "amount",
        "account_name",
    }

    produced_columns: ClassVar[set[str]] = {
        "trade_date",
        "symbol",
        "transaction_type",
        "quantity",
        "amount",
        "account_name",
    }

    preserves_schema: ClassVar[bool] = True

    def execute(
        self,
        context: ExecutionContext,
        payload: BatchPayload,
        params: NormalizeInvestmentTransactionsParams,
    ) -> BatchPayload:
        df = payload.frame

        if params.trim_account_name and "account_name" in df.columns:
            df = df.with_columns(pl.col("account_name").str.strip_chars())

        if params.uppercase_symbol and "symbol" in df.columns:
            df = df.with_columns(pl.col("symbol").str.to_uppercase())

        if params.drop_zero_quantity and "quantity" in df.columns:
            df = df.filter(pl.col("quantity") != 0)

        if "transaction_type" in df.columns:
            df = df.filter(
                pl.col("transaction_type").is_in(params.allowed_transaction_types)
            )

        return payload.with_frame(df)
```

---

# How the config links to this hook

There are **two good options**.

## Option A — Best practice: registry-based reference by `hook_name`

This is the one I recommend.

---

## 3) In `project.yaml`, declare hook search paths

```yaml
project:
  project_id: personal_finance_etl
  name: Personal Finance ETL

plugins:
  hook_search_paths:
    - "semantic_finance_etl.user_hooks"
    - "./user_hooks"
```

At startup, the app:

- scans these paths
- imports Python modules
- finds classes implementing the hook contract
- registers them by `hook_name`

So from `investment_transformations.py`, it registers:

```text
normalize_investment_transactions
```

---

## 4) In `investment_transactions.yaml`, reference only the hook name

```yaml
table_name: investment_transactions
table_kind: canonical

columns:
  - name: trade_date
    type: date
  - name: symbol
    type: str
  - name: transaction_type
    type: str
  - name: quantity
    type: decimal
  - name: amount
    type: decimal
  - name: account_name
    type: str

hooks:
  post_append:
    - hook: normalize_investment_transactions
      order: 10
      enabled: true
      params:
        drop_zero_quantity: true
        uppercase_symbol: true
        trim_account_name: true
        allowed_transaction_types:
          - BUY
          - SELL
          - DIVIDEND
          - BONUS
```

That’s it.

The engine resolves:

```text
normalize_investment_transactions
→ found in registry
→ implemented by investment_transformations.NormalizeInvestmentTransactionsHook
→ validate params using NormalizeInvestmentTransactionsParams
→ execute at POST_APPEND stage
```

---

# Why this is the best design

Because table config stays clean.

Your table YAML does **not** become this:

```yaml
hook_file: ./user_hooks/investment_transformations.py
class_name: NormalizeInvestmentTransactionsHook
```

for every hook.

That would work, but it gets noisy and brittle.

Instead, the better mental model is:

- Python file defines the implementation
- hook registry discovers it
- config references the stable business-facing hook id

---

# Option B — Explicit module/class reference

If you want very explicit linking, you can allow config to point directly to module + class.

Example:

```yaml
hooks:
  post_append:
    - hook_ref:
        module: user_hooks.investment_transformations
        class: NormalizeInvestmentTransactionsHook
      order: 10
      params:
        drop_zero_quantity: true
        uppercase_symbol: true
```

This works too, and is useful when:

- you do not want auto-discovery
- you want zero ambiguity
- you are debugging local development

But I would use this as a **secondary supported mode**, not the default.

---

# Best architecture: support both

I’d design it like this:

## Preferred mode
Use stable registry id:

```yaml
hook: normalize_investment_transactions
```

## Fallback mode
Use explicit import reference:

```yaml
hook_ref:
  module: user_hooks.investment_transformations
  class: NormalizeInvestmentTransactionsHook
```

That gives flexibility without cluttering normal configs.

---

# What the config model would look like

A good `HookBindingConfig` model could look like this:

```python
from pydantic import BaseModel, Field
from typing import Any


class ExplicitHookReference(BaseModel):
    module: str
    class_name: str = Field(alias="class")


class HookBindingConfig(BaseModel):
    hook: str | None = None
    hook_ref: ExplicitHookReference | None = None

    order: int = 100
    enabled: bool = True
    params: dict[str, Any] = Field(default_factory=dict)

    fail_behavior: str = "fail_run"
    timeout_seconds: int | None = None
```

Validation rules:

- exactly one of `hook` or `hook_ref` must be provided
- if `hook` is used, it must exist in registry
- if `hook_ref` is used, the class must be importable
- the hook’s declared `stage` must match the config section where it is bound
- params must validate against the hook’s `params_model`

---

# How the engine resolves it internally

Here is the runtime flow.

## Step 1 — load project config
It reads:

```yaml
plugins:
  hook_search_paths:
    - "./user_hooks"
```

## Step 2 — scan and import hooks
The registry imports `investment_transformations.py`

## Step 3 — register hook metadata
It finds:

```python
hook_name = "normalize_investment_transactions"
stage = HookStage.POST_APPEND
params_model = NormalizeInvestmentTransactionsParams
```

## Step 4 — load table config
It sees:

```yaml
hooks:
  post_append:
    - hook: normalize_investment_transactions
```

## Step 5 — binding resolver validates
The engine checks:

- does this hook exist?
- does its stage equal `post_append`?
- are the params valid?
- are required columns compatible with the target pipeline/table?

## Step 6 — execute during pipeline run
When the pipeline reaches `post_append`, it invokes the hook.

---

# Concrete example with all files together

## `project.yaml`

```yaml
project:
  project_id: personal_finance_etl

plugins:
  hook_search_paths:
    - "./user_hooks"
```

---

## `user_hooks/investment_transformations.py`

```python
from typing import ClassVar
from pydantic import BaseModel
import polars as pl

from semantic_finance_etl.contracts.hook import TableHook
from semantic_finance_etl.domain.enums.hook_stage import HookStage
from semantic_finance_etl.domain.models.hook_payloads import BatchPayload
from semantic_finance_etl.domain.models.execution_context import ExecutionContext


class AssignInvestmentIdsParams(BaseModel):
    id_prefix: str = "INV"


class AssignInvestmentIdsHook(TableHook[BatchPayload, BatchPayload, AssignInvestmentIdsParams]):
    hook_name: ClassVar[str] = "assign_investment_ids"
    stage: ClassVar[HookStage] = HookStage.PRE_LOAD
    params_model = AssignInvestmentIdsParams

    required_columns: ClassVar[set[str]] = {"trade_date", "symbol", "account_name"}
    produced_columns: ClassVar[set[str]] = {"canonical_id"}

    preserves_schema: ClassVar[bool] = False

    def execute(
        self,
        context: ExecutionContext,
        payload: BatchPayload,
        params: AssignInvestmentIdsParams,
    ) -> BatchPayload:
        df = payload.frame.with_columns(
            pl.concat_str(
                [
                    pl.lit(params.id_prefix),
                    pl.lit("_"),
                    pl.col("account_name"),
                    pl.lit("_"),
                    pl.col("symbol"),
                    pl.lit("_"),
                    pl.col("trade_date").cast(pl.Utf8),
                ]
            ).alias("canonical_id")
        )
        return payload.with_frame(df)
```

---

## `configs/tables/investment_transactions.yaml`

```yaml
table_name: investment_transactions
table_kind: canonical

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
  - name: amount
    type: decimal
  - name: account_name
    type: str

hooks:
  pre_load:
    - hook: assign_investment_ids
      order: 10
      params:
        id_prefix: INV
```

---

# If one file contains many hooks

That is perfectly fine.

For example `investment_transformations.py` can contain:

- `normalize_investment_transactions`
- `deduplicate_investment_rows`
- `assign_investment_ids`
- `build_investment_positions`

Each has a unique `hook_name`.

Then different tables or stages can reference them independently.

Example:

```yaml
hooks:
  post_append:
    - hook: normalize_investment_transactions
      order: 10

    - hook: deduplicate_investment_rows
      order: 20

  pre_load:
    - hook: assign_investment_ids
      order: 30
```

---

# How strong typing helps here

Because each hook carries its own typed param model, the engine can do this before runtime:

## validate param shape
If config says:

```yaml
params:
  drop_zero_quantity: "yes"
```

and the param model expects `bool`, validation can fail early or coerce safely depending on your rule.

## validate hook-stage compatibility
If `assign_investment_ids` is declared as `PRE_LOAD`, but you place it under `post_append`, the config should fail.

## validate schema compatibility
If the hook requires columns:

```python
required_columns = {"trade_date", "symbol", "account_name"}
```

and the table/pipeline cannot provide them, startup validation should flag it.

That is how hooks stay powerful without becoming dangerous.

---

# My recommended config syntax

If I were locking this architecture, I would use this exact pattern.

## In code
Each hook declares:

- `hook_name`
- `stage`
- `params_model`
- `required_columns`
- `produced_columns`

## In project config
Declare:

```yaml
plugins:
  hook_search_paths:
    - "./user_hooks"
```

## In table/source config
Reference:

```yaml
hook: normalize_investment_transactions
```

Not file names directly.

---

# Why not reference the file directly every time?

Because this becomes painful fast:

```yaml
hooks:
  pre_load:
    - file: ./user_hooks/investment_transformations.py
      class: AssignInvestmentIdsHook
```

Problems:

- noisy YAML
- renaming files breaks many configs
- difficult for UI dropdowns
- awkward for hook registry
- harder to version and document

So use **stable logical ids** in configs, not physical file paths.

---

# Best-practice mental model

Think of it like this:

## Python file
Implementation container

## Hook class
Typed executable unit

## `hook_name`
Stable public identifier

## Config
Binding/orchestration layer

So the config should say:

> “For the investment table, run `assign_investment_ids` at `pre_load` with these params.”

Not:

> “Import this exact class from this exact file path and hope the folder never changes.”

---

# Short answer

If you create a typed hook inside `investment_transformations.py`, the best way to link it is:

1. register/discover that file through a global `hook_search_paths` setting
2. give the hook class a stable `hook_name`
3. reference that `hook_name` inside the investment table config

Example:

```yaml
hooks:
  pre_load:
    - hook: assign_investment_ids
      params:
        id_prefix: INV
```

with the Python class declaring:

```python
hook_name = "assign_investment_ids"
```

---
