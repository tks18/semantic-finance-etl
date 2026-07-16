# `semantic_finance_etl`

## 1. Goal

Build a **config-driven ETL framework** where:

- config controls orchestration
- Python hooks perform transformations
- source discovery remains first-class
- tables are schema-driven
- runtime is local-first
- SQLite is the serving layer
- **Polars `LazyFrame` is the core execution substrate**
- schema contracts are explicit and enforceable
- materialization happens only at defined runtime boundaries
- the final design supports canonical, derived, and semantic data layers

---

## 2. Final Build Order

Build the project in this order:

1. **LazyFrame-native data foundation**
2. **Config foundation**
3. **Hook contracts + registry**
4. **Source discovery / selection / grouping / readers**
5. **LazyFrame-native orchestration pipeline**
6. **Validation + SQLite loading**
7. **DLQ + lineage + run tracking**
8. **Derived table pipeline**
9. **Semantic layer**
10. **UI**
11. **Hardening + testing**

---

## 3. Current Status Baseline

You should consider these as current foundation areas to refine into the final architecture:

- config models
- YAML loaders
- config validation
- hook contracts
- hook registry
- hook binding resolver
- hook runner
- source contracts
- first source implementations
- first orchestration path
- first validation + SQLite load path

All of these should now be aligned to the same runtime assumption:

- transformation payloads carry **`pl.LazyFrame`**
- schema is tracked explicitly
- collection occurs only at designated boundaries

---

## 4. Remaining Project Roadmap

---

## Phase A — Establish the Data Execution Backbone

### Objective
Make the runtime model unambiguous and stable by defining the engine around:

- `pl.LazyFrame`
- explicit schema contracts
- typed payloads
- explicit materialization boundaries

### Files to define or finalize

#### `domain/models/`
- `data_schema.py`
- `frame_contracts.py`
- `hook_payloads.py`
- `hook_results.py`
- later: `runtime_table_definition.py`

### What they should contain

#### `data_schema.py`
- logical types
- column schema definitions
- nullability
- precision / scale
- aliases / tags
- schema comparison helpers
- conversion to Polars schema
- schema inference from Polars schema

#### `frame_contracts.py`
- execution engine metadata
- required columns
- provided columns
- schema mutation behavior
- cardinality behavior
- materialization policy

#### `hook_payloads.py`
- `ExecutionContext`
- `ReadPayload`
- `BatchPayload`
- `ValidatedBatchPayload`
- `LoadPayload`
- `DerivedBuildPayload`
- `SemanticProjectionPayload`
- `frame: pl.LazyFrame | None`
- `schema: DataSchema | None`

#### `hook_results.py`
- `HookExecutionResult`
- `HookMetrics`
- `HookSchemaImpact`
- warnings
- execution metadata

### Acceptance criteria
- every transformation-capable payload uses `pl.LazyFrame`
- schema can be inferred or attached explicitly
- contracts can validate required/provided columns
- payload methods make collection explicit and controlled

---

## Phase B — Stabilize the Config Foundation

### Objective
Make configuration strict, composable, and cleanly separated from runtime logic.

### Files to finalize / refine

#### `config/models/`
- `project_config.py`
- `source_config.py`
- `table_config.py`
- `transform_config.py`
- `semantic_config.py`
- `runtime_config.py`

### What they should contain
- strict Pydantic config models
- good defaults
- declarative orchestration only
- no runtime execution logic
- no registry lookup logic
- local validation only

#### `config/loaders/`
- `yaml_loader.py`
- `project_loader.py`

### What they should contain
- split-folder config loading
- merge logic
- clear error handling
- support both inline and split-file configs

#### `config/services/`
- `config_validation_service.py`
- `project_config_service.py`
- later: `config_resolution_service.py`
- later: `hook_binding_validation_service.py`

### What they should contain
- cross-reference validation
- defaults normalization
- relative path resolution
- future registry-aware validation

### Acceptance criteria
- one config folder loads consistently
- duplicate IDs fail fast
- missing table refs fail fast
- invalid hook stage placement fails fast

---

## Phase C — Make Hook Execution Enterprise-Grade

### Objective
Move from “hooks can run” to “hooks are safe, typed, auditable, and pluggable.”

### Files

#### `contracts/`
- `hook.py`

### Should contain
- `BaseHook`
- `SourceHook`
- `TableHook`
- `DerivedTableHook`
- `SemanticHook`
- class-level metadata:
  - `hook_name`
  - `stage`
  - `params_model`
  - `payload_type`
  - `frame_contract`
  - `input_schema`
  - `output_schema`

### Hook behavior
Hooks should operate on `pl.LazyFrame` payloads and return structured results.

#### `domain/models/`
- `hook_payloads.py`
- `hook_results.py`

### Should contain
- `ExecutionContext`
- `ReadPayload`
- `BatchPayload`
- `ValidatedBatchPayload`
- `LoadPayload`
- `DerivedBuildPayload`
- `SemanticProjectionPayload`
- `HookExecutionResult`
- `HookMetrics`
- `HookSchemaImpact`

#### `infrastructure/plugins/`
- `hook_loader.py`
- `local_plugin_registry.py`

### Should contain
- module loading from paths
- hook class discovery
- duplicate `hook_name` prevention
- registry listing and lookup
- frame contract metadata exposure

#### `etl/hooks/`
- `hook_binding_resolver.py`
- `hook_context_factory.py`
- `hook_runner.py`

### Should contain
- config binding resolution
- params validation from `params_model`
- stage validation
- ordered execution
- output chaining from one hook to next
- contract-aware schema checks before execution
- explicit stage-level observability

### Acceptance criteria
- hook config resolves correctly
- bad params fail before runtime
- wrong stage binding fails
- one stage can execute multiple hooks in order
- hooks transform `LazyFrame` plans without hidden collection

---

## Phase D — Complete the Base Source Pipeline

### Objective
Support the full ingestion path cleanly and natively in the same execution model.

### Contracts

#### `contracts/`
- `source_discoverer.py`
- `source_selector.py`
- `source_grouper.py`
- `source_reader.py`

### Implementations

#### `infrastructure/discovery/`
- `filesystem_discoverer.py`

#### `infrastructure/selection/`
- `latest_modified_selector.py`
- later: `all_files_selector.py`
- later: `top_n_latest_selector.py`

#### `infrastructure/grouping/`
- `single_group_grouper.py`
- later: `parent_folder_grouper.py`
- later: `date_partition_grouper.py`

#### `infrastructure/readers/`
- `sqlite_query_reader.py`
- later: `csv_reader.py`
- later: `excel_reader.py`
- later: `json_reader.py`
- later: `parquet_reader.py`

### Reader behavior
Readers should return `ReadPayload` with:

- `frame: pl.LazyFrame`
- `schema: DataSchema | None`
- asset metadata
- reader metadata

### Acceptance criteria
- assets are discovered from filesystem
- latest file can be selected
- assets can be grouped
- source file can be read into typed `LazyFrame` payloads

---

## Phase E — Build the LazyFrame-Native Orchestration Pipeline

### Objective
Run the ingestion pipeline end-to-end without breaking the lazy execution model.

### Files

#### `infrastructure/factories/`
- `source_component_factory.py`

#### `tables/`
- `configured_table_pipeline.py`

#### `etl/orchestration/`
- `pipeline_executor.py`

### Pipeline flow
For one source → one target table:

1. discover assets
2. select assets
3. group assets
4. read asset group into `ReadPayload`
5. run `post_read` hooks
6. unify schemas where needed
7. append using lazy concat
8. run `pre_append` hooks
9. run `post_append` hooks
10. run validation boundary
11. run `pre_load` hooks
12. collect only where load requires it
13. persist to target
14. run `post_load` hooks

### Append behavior
Use Polars-native lazy concatenation:

- `pl.concat([...], how="vertical_relaxed")`
- with schema harmonization beforehand where necessary

### Acceptance criteria
- a full in-memory pipeline works with `LazyFrame`
- hook outputs chain without materializing by default
- append logic remains lazy
- collect boundaries are explicit and inspectable

---

## Phase F — Validation, Load, DLQ, Lineage, Tracking

### Objective
Make the pipeline safe, auditable, and operationally reliable.

### Files

#### `domain/models/`
- `runtime_table_definition.py`

### Should contain
- runtime column definitions
- primary key fields
- load mode
- record hash flag
- table config to runtime compiler

#### `etl/validation/`
- `validation_service.py`

### Should contain
- schema checks
- required column checks
- nullability checks
- type compatibility checks
- uniqueness checks where configured
- valid/invalid split
- validation summary

### Validation behavior
Validation should use two levels:

#### Lazy/schema validation
- check shape before collecting where possible
- validate required columns
- validate schema compatibility
- validate hook input/output contracts

#### Materialized/data validation
- collect only when row-level inspection is needed
- split into valid/invalid frames
- produce `ValidatedBatchPayload`

#### `infrastructure/database/`
- `sqlite_writer.py`

### Should contain
- table creation
- type mapping
- append
- replace
- upsert

#### `etl/loading/`
- `load_service.py`

### Should contain
- validated payload to load payload conversion
- explicit collection at load boundary
- call into SQLite writer
- return load summary

#### `etl/dlq/`
- `dlq_service.py`

### Should contain
- invalid row persistence
- stage name
- source ID
- table name
- raw row payload
- error message
- run ID

#### `etl/lineage/`
- `lineage_service.py`

### Should contain
- file lineage
- hook lineage
- stage lineage
- output lineage references

#### `etl/tracking/`
- `run_tracking_service.py`

### Should contain
- run start/end records
- row counts
- source counts
- table counts
- duration
- status

### Acceptance criteria
- valid rows reach SQLite
- invalid rows go to DLQ
- run can be traced
- hook execution can be traced
- collection occurs only at validation/load boundaries or other explicitly declared boundaries

---

## 5. Runtime Data Model

### Core rule
All transformation-capable runtime data should be carried as **`pl.LazyFrame`**.

### Payload strategy
- `ReadPayload.frame` → `pl.LazyFrame`
- `BatchPayload.frame` → `pl.LazyFrame`
- `ValidatedBatchPayload.valid_frame` → `pl.LazyFrame`
- `ValidatedBatchPayload.invalid_frame` → `pl.LazyFrame | None`

### Materialization boundaries
Collection should happen only when a stage genuinely requires realized data, such as:

- row-level validation checks
- SQLite persistence
- export generation
- certain reconciliation outputs
- explicitly declared non-lazy hooks

### Result
The runtime model remains uniform and predictable across readers, hooks, append, derived builds, and semantic shaping.

---

## 6. Polars Execution Strategy

### Runtime standard
Use Polars expressions as the default transformation language.

### Preferred operations
- `select`
- `with_columns`
- `filter`
- `join`
- `group_by().agg()`
- `sort`
- `unique`
- `cast`
- `when().then().otherwise()`

### Avoid by default
- row-wise Python loops
- hidden `.collect()`
- map-style Python transformations unless unavoidable

### Why this matters
It keeps the system:

- optimizable
- composable
- scalable
- inspectable
- consistent across all stages

---

## 7. Source Reader Design

### Reader contract
Readers should not return row dictionaries as the main data structure.

### Required behavior
A reader must return:

- `ReadPayload`
- `frame: pl.LazyFrame`
- `schema` inferred or validated
- source metadata
- reader metadata

### Example reader behavior
#### `sqlite_query_reader.py`
- locate SQLite asset
- execute query
- read into Polars `DataFrame`
- immediately convert to `.lazy()`
- infer schema or apply configured schema
- return `ReadPayload`

### Acceptance criteria
- readers expose a uniform `LazyFrame` payload contract
- downstream hook execution does not need reader-specific branching

---

## 8. Hook Execution Model

### Hook input/output
Hooks should accept and return payloads that wrap `pl.LazyFrame`.

### Hook implementation style
A typical hook should:

1. read the existing lazy plan
2. apply Polars lazy expressions
3. return a new payload with the updated lazy plan
4. return structured metrics and warnings

### Example contract expectations
Hooks should declare:

- required input columns
- guaranteed output columns
- schema mutation behavior
- cardinality behavior
- materialization policy

### Acceptance criteria
- hook chaining remains lazy by default
- output plans remain composable
- schema changes are explicit and traceable

---

## 9. Validation Strategy

### Validation layers

#### Schema validation
Done before or without collecting where possible:
- required columns exist
- types are compatible
- primary keys are present
- hook contracts are satisfied

#### Data validation
Done at a controlled execution boundary:
- null checks
- uniqueness checks
- allowed value checks
- business rule checks
- reconciliation checks

### Output
Validation should produce:

- `ValidatedBatchPayload.valid_frame`
- `ValidatedBatchPayload.invalid_frame`
- validation issues
- validation summary

---

## 10. Load Strategy

### Load behavior
SQLite loading should operate from materialized data only.

### Load flow
1. receive validated payload
2. collect the valid lazy frame
3. apply final load-ready shaping if needed
4. write to SQLite
5. return structured load metrics

### SQLite writer responsibilities
- generate DDL from runtime table definition
- create or evolve target table as configured
- write rows efficiently
- support append / replace / upsert

---

## 11. Derived Table Pipeline

### Objective
Support dependency-aware analytical tables.

### Files

#### `tables/`
- `derived_table_pipeline.py`

#### `etl/orchestration/`
- `dag_builder.py`
- `dependency_resolver.py`

### Should contain
- dependency graph build
- topological ordering
- rebuild on dependency change
- hook-based derived build execution

### Execution model
Derived builds should remain in lazy form for joins, aggregations, windows, and time-series logic until validation/load boundaries.

### Acceptance criteria
- derived tables can depend on canonical tables
- derived hooks build outputs correctly
- build order respects dependencies
- lazy execution plans remain intact across dependency chains

---

## 12. Semantic Layer

### Objective
Turn structured rows into searchable semantic content.

### Files

#### `semantic/`
- `projection_service.py`
- `chunking_service.py`
- `indexing_service.py`
- later: `embedding_service.py`

#### `config/models/`
- `semantic_config.py` already exists, extend as needed

### Should contain
- row-to-document projection
- template rendering
- chunking
- metadata tagging
- future embeddings

### Execution model
Where semantic preparation requires table shaping, it should operate from lazy table reads and collect only at document generation or indexing boundaries.

### Acceptance criteria
- semantic configs resolve
- source table rows become semantic docs
- docs can be chunked and indexed

---

## 13. UI

### Objective
Make config pleasant, not painful.

### Files / modules

#### `ui/`
- `app.py`
- `views/`
- `controllers/`
- `viewmodels/`
- `services/`

### UI should support
- config editing
- hook registry browsing
- typed param forms
- source discovery preview
- pipeline execution
- run history
- DLQ inspection
- lineage inspection

### Acceptance criteria
- user can create/edit source config
- user can bind hooks from registry
- params validate via schema
- run output is inspectable

---

## 14. Hardening

### Objective
Make the system durable and maintainable.

### Files / areas
- `tests/unit/`
- `tests/integration/`
- `tests/fixtures/`
- docs
- logging
- sample starter projects

### Must include
- golden dataset tests
- config loading tests
- hook contract tests
- pipeline integration tests
- SQLite load tests
- derived table tests
- schema contract tests
- lazy pipeline boundary tests

---

## 15. Recommended Immediate Next Coding Order

If you are coding from this document, use this order now:

1. `domain/models/data_schema.py`
2. `domain/models/frame_contracts.py`
3. `domain/models/hook_payloads.py`
4. `domain/models/hook_results.py`
5. refactor `contracts/hook.py` around frame contracts
6. refactor `contracts/source_reader.py` to return `ReadPayload[LazyFrame]`
7. refactor `infrastructure/readers/sqlite_query_reader.py`
8. refactor `tables/configured_table_pipeline.py` to append lazily
9. refactor `etl/validation/validation_service.py`
10. refactor `etl/loading/load_service.py`
11. refactor `infrastructure/database/sqlite_writer.py`
12. add `etl/dlq/dlq_service.py`
13. add `etl/lineage/lineage_service.py`
14. add `etl/tracking/run_tracking_service.py`
15. add derived table pipeline
16. add semantic layer
17. add UI

---

## 16. Final Recommended Architecture State

At the end, the system should look like this:

### Config
- declarative orchestration only

### Hooks
- strongly typed
- Python-based
- schema-aware
- stage-aware
- `LazyFrame`-native

### Source system
- discoverer
- selector
- grouper
- reader returning `LazyFrame`

### Transformation engine
- Polars-first
- `LazyFrame`-native across runtime stages
- explicit boundary collection only

### Validation/load
- schema-driven
- SQLite persistence
- DLQ-supported

### Governance
- lineage
- run tracking
- auditability

### Advanced features
- derived DAG tables
- semantic indexing
- UI-driven config experience

---

## 17. Non-Negotiable Rules

1. config must not become a transformation DSL
2. hooks must stay typed
3. discovery must remain first-class
4. transformation payloads must remain `LazyFrame`-based
5. collect boundaries must be explicit
6. SQLite load must happen from materialized data
7. validation and load must stay schema-driven
8. every hook execution should eventually be traceable
9. schema mutations must be declared, not hidden

---

## 18. Practical Advice While Coding

- keep models simple
- keep services responsible for cross-object logic
- avoid circular imports
- use Polars expressions by default
- keep `.collect()` visible and deliberate
- get one happy path working before generalizing
- write one sample project config and keep testing against it
- keep one sample hook module and one sample SQLite source as your regression path

---

## 19. Suggested Milestones

### Milestone 1
LazyFrame-native data foundation works

### Milestone 2
Config system works

### Milestone 3
Hook registry + resolver works

### Milestone 4
Source pipeline works with `LazyFrame`

### Milestone 5
End-to-end orchestration works with lazy append and hook chaining

### Milestone 6
Validation + SQLite load works

### Milestone 7
DLQ + lineage + tracking work

### Milestone 8
Derived tables work

### Milestone 9
Semantic layer works

### Milestone 10
UI works

---

## 20. Final Summary

Build the project in this sequence:

**data backbone → config → hooks → source runtime → orchestration → validation/load → auditability → derived tables → semantics → UI**

The system should be:

- config-driven
- hook-extensible
- schema-aware
- `LazyFrame`-native
- SQLite-served
- auditable
- ready for canonical, derived, and semantic pipelines

---
