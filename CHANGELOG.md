# Changelog

All notable changes to this project will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

### [0.1.1-10](https://github.com/tks18/semantic-finance-etl/compare/0.1.1-9...0.1.1-10) (2026-07-16)


### CI 🛠

* **gitignore:** add mypy and pytest directory in gitignore ([bc5c76f](https://github.com/tks18/semantic-finance-etl/commit/bc5c76f12586c6b94104bb8ba5fd8303f149dfbc))


### Features 🔥

* **config/models:** add primary key to semantic config ([7d1d5c4](https://github.com/tks18/semantic-finance-etl/commit/7d1d5c466ea6425a5a8b29b17444ee15cdf7e790))
* **config/models:** add support for foreign key configurations ([5188d3e](https://github.com/tks18/semantic-finance-etl/commit/5188d3e1df9c26a960748797fb8be827bac247a9))
* **config/models:** add support for log directory in model ([c194150](https://github.com/tks18/semantic-finance-etl/commit/c194150b8f6af13220861ccaa8627d286bdb3b45))
* **contracts:** rewrite to support polars dataschema ([93f85d4](https://github.com/tks18/semantic-finance-etl/commit/93f85d41adf99b24634331465af3ab40cc7b0df3))
* **domain/models:** rewrite hook_payloads.py ([b3fd986](https://github.com/tks18/semantic-finance-etl/commit/b3fd9862f4ef1b6ef63bd611b71f3a6e38ff2102))
* **domain/models:** rewrite hook-results.py ([c61cb77](https://github.com/tks18/semantic-finance-etl/commit/c61cb77c205ac9db12f5ae3575631058ff540f85))
* **domain/models:** rewrite runtime_table_definition.py ([574f7f9](https://github.com/tks18/semantic-finance-etl/commit/574f7f94fd77730aef8cc6b466650abf9eb7f374))
* **etl/dlq:** add dlq_service.py ([849c4da](https://github.com/tks18/semantic-finance-etl/commit/849c4daa92d0e4acd650d0f930b3736614d98977))
* **etl/hooks:** add a builtin_hooks module ([22bf076](https://github.com/tks18/semantic-finance-etl/commit/22bf07601bfa3fe76e3bb505d072bb7301bd19ab))
* **etl/lineage:** add lineage_service.py ([ebdf6a8](https://github.com/tks18/semantic-finance-etl/commit/ebdf6a82011fa408b27d27964689d5a70b4e2632))
* **etl/loading:** enable loading service to support polars lf/df ([1202ee5](https://github.com/tks18/semantic-finance-etl/commit/1202ee50e83e063a1b290f2774c75fc58fd5dae7))
* **etl/orchestration:** add dag_builder.py ([c98c176](https://github.com/tks18/semantic-finance-etl/commit/c98c176d8e38b5d940ffe7a27e6df67c88e1fd0d))
* **etl/orchestration:** edit pipeline_executor.py ([2d5c1d0](https://github.com/tks18/semantic-finance-etl/commit/2d5c1d0019e72112fc556b8c7f6b7730625ea5b0))
* **etl/semantic:** add chunking_service.py ([c4710d6](https://github.com/tks18/semantic-finance-etl/commit/c4710d64b2bb76f6cd496783aa7b58a26f4f84c7))
* **etl/semantic:** add indexing_service.py ([ad0eb4a](https://github.com/tks18/semantic-finance-etl/commit/ad0eb4a33728f63828b110008063148d88226c4e))
* **etl/semantic:** add projection_service.py ([913dab1](https://github.com/tks18/semantic-finance-etl/commit/913dab1a89b8f4919da8501e0797c02896e93ab2))
* **etl/tracking:** add tracking_services.py ([1541fcd](https://github.com/tks18/semantic-finance-etl/commit/1541fcdc033b3b73499cceec2a48d4277d7431ac))
* **etl/validation:** add support for polars for validation service ([4f970c5](https://github.com/tks18/semantic-finance-etl/commit/4f970c5f35c6dcbf1a8978c6ff1760860255c6fc))
* **infra/database:** enable sqlite write to process polars dataframes ([afaaa8b](https://github.com/tks18/semantic-finance-etl/commit/afaaa8b7458069bd62be237652c554eae776fdab))
* **infra/plugins:** enable builtin hooks using plugin registry ([f8f4835](https://github.com/tks18/semantic-finance-etl/commit/f8f4835807886ad68e62773fc30f0f81c9b9ec4a))
* **infra/readers:** support sqlite reader with polars lazyframe support ([41c4873](https://github.com/tks18/semantic-finance-etl/commit/41c487390a4461eb55d98ca4209170aacc7b48ce))
* **tables:** add derived_table_pipeline.py ([9dcb257](https://github.com/tks18/semantic-finance-etl/commit/9dcb257c037e60b3e43119254f352730c66b3e59))
* **tables:** support for polars dataschema ([dffb74e](https://github.com/tks18/semantic-finance-etl/commit/dffb74eb7b1f5d636b1fe20f802d8f1c86efbbf6))
* **utils:** add a shared logging module ([c97422d](https://github.com/tks18/semantic-finance-etl/commit/c97422db3a27383d543ee8769c994427e63ccc45))


### Tests 🧪

* **adhoc:** add some adhoc tests for validating the output ([39886cb](https://github.com/tks18/semantic-finance-etl/commit/39886cb3e82e23add7cd2b97e3e5b2367e3b2075))
* **conftest:** setup pytest common fixtures ([7ed0953](https://github.com/tks18/semantic-finance-etl/commit/7ed0953228af54b93c9f833f78693edace6e1d0d))
* remove test outputs from git ([0e9c555](https://github.com/tks18/semantic-finance-etl/commit/0e9c555dbb0d01849aa906d49acdc996f97854fc))
* **tests/config:** add proper pytest cases for config based operations ([9c11732](https://github.com/tks18/semantic-finance-etl/commit/9c11732ead68a771ca23b06db24f81d62dda97e1))
* **tests/config:** add pytest for simple config parsing ([f8178f0](https://github.com/tks18/semantic-finance-etl/commit/f8178f0f4f44436fecfd47887997bfd3cf2ffaf9))
* **tests/etl:** add domain and validation service related tests ([75b97f0](https://github.com/tks18/semantic-finance-etl/commit/75b97f020737a6bd93095d01b3cf19d2d86a8899))
* **tests/etl:** add e2e scenarios for testing ([8230804](https://github.com/tks18/semantic-finance-etl/commit/82308046a551b558e739f12cc653b2dc747739ea))
* **tests/etl:** add test cases for loading into sqlite ([8f39c13](https://github.com/tks18/semantic-finance-etl/commit/8f39c13b52368096033a5ca581d5a69f42dd1dd0))
* **tests/etl:** add tests for dag resolver ([f054b14](https://github.com/tks18/semantic-finance-etl/commit/f054b149cdfb7849deb36d5a52f9fbb87924aa08))
* **tests/etl:** add tests for lineage, tracking, dlq services ([f5bcaa5](https://github.com/tks18/semantic-finance-etl/commit/f5bcaa5ea469d7a60d5d7ccbf1e62555b27054a1))
* **tests/etl:** add tests for reader pipeline ([eee178b](https://github.com/tks18/semantic-finance-etl/commit/eee178b27afaf8dfd1a144559b3ce1d06af33ea8))
* **tests/etl:** rewrite pipeline executor to pytest support ([e95416e](https://github.com/tks18/semantic-finance-etl/commit/e95416e874df950829ec44ddd08713aea99a35d3))
* **tests/hooks:** rewrite for pytest support ([cbfb601](https://github.com/tks18/semantic-finance-etl/commit/cbfb601e548ad60d4434348f61daa3f98c189e1d))
* **tests/hooks:** rewrite for pytest support ([5d292e3](https://github.com/tks18/semantic-finance-etl/commit/5d292e3ca0fe981662d6c4f3dc896d88bc25eed0))
* **tests/samples:** add a complex config for testing the entire app e2e ([c3728dc](https://github.com/tks18/semantic-finance-etl/commit/c3728dc3b286db161a5107c693c10a256fca6ecc))
* **tests/semantic:** add test cases for semantic services testing ([b87310d](https://github.com/tks18/semantic-finance-etl/commit/b87310d1f2bcf57f42ea3e4d25d9bc7ee7c8e164))

### [0.1.1-9](https://github.com/tks18/semantic-finance-etl/compare/0.1.1-8...0.1.1-9) (2026-07-16)


### Tests 🧪

* **tests/samples:** fix paths of the sample tables ([76182fc](https://github.com/tks18/semantic-finance-etl/commit/76182fcc016a567ec3027abe9042e2e271306700))

### [0.1.1-8](https://github.com/tks18/semantic-finance-etl/compare/0.1.1-7...0.1.1-8) (2026-07-15)


### Features 🔥

* **domain/models:** add data_schema.py domain model ([b7891aa](https://github.com/tks18/semantic-finance-etl/commit/b7891aa90d0c3a652e9e5401386e7714951cfe22))
* **domain/models:** add frame_contracts.py domain model ([c6bd80f](https://github.com/tks18/semantic-finance-etl/commit/c6bd80fc00ed54e85712b6fcb162f2db339ab245))
* **domain/models:** add runtime_table_definition.py model ([5fee1ec](https://github.com/tks18/semantic-finance-etl/commit/5fee1ece6eae1c376518fb40c6780f55b1149866))
* **etl/loading:** add load_service etl module ([6392d19](https://github.com/tks18/semantic-finance-etl/commit/6392d198d0c771bee660666ac1ee8b0a08b7d83f))
* **etl/orchestration:** add pipeline_executor.py etl module ([497a9bd](https://github.com/tks18/semantic-finance-etl/commit/497a9bdd0e9da27d1f5b8f1469023b7b9b6d6df1))
* **etl/validation:** add validation_service.py etl module ([3541e5c](https://github.com/tks18/semantic-finance-etl/commit/3541e5c545248304a7430ce4af5abb487952510e))
* **infra/database:** add sqlite_writer.py ([a2fec5c](https://github.com/tks18/semantic-finance-etl/commit/a2fec5c522c45c9ed625e33dfe9b5b9241deb068))
* **infra/factories:** add source_component_factory.py ([15b250e](https://github.com/tks18/semantic-finance-etl/commit/15b250e54fbad8acccfb298427f235f7841277a7))
* **tables:** add configured_table_pipeline.py table module ([79c4214](https://github.com/tks18/semantic-finance-etl/commit/79c42148c4a3ddf88d6143550e81028482e12a29))


### Tests 🧪

* **tests/cases:** add tests for hooks, also upload the output db for comparison ([ec7c689](https://github.com/tks18/semantic-finance-etl/commit/ec7c689092f9c95fa23dde56cc94de8ebd1dbcf0))
* **tests/cases:** add various test cases for etl pipelines ([8565224](https://github.com/tks18/semantic-finance-etl/commit/8565224c090be58983766dacae6a6190d9a6e961))


### Docs 📃

* add doc for current state of project and understanding of future implementations ([064073e](https://github.com/tks18/semantic-finance-etl/commit/064073e7b5bbb726e2a7d1cd3cbc82ee529832b1))
* add folder_representation doc for understanding ([fdf080a](https://github.com/tks18/semantic-finance-etl/commit/fdf080af28d240b3e073590f69f61a7461a9a681))

### [0.1.1-7](https://github.com/tks18/semantic-finance-etl/compare/0.1.1-6...0.1.1-7) (2026-07-15)


### Features 🔥

* **infra/discovery:** add filesystem_discoverer infra module ([c539c06](https://github.com/tks18/semantic-finance-etl/commit/c539c06c89f0c6814127a92da1c65bb560d10c15))
* **infra/grouper:** add single_group_grouper.py infra module ([c89c590](https://github.com/tks18/semantic-finance-etl/commit/c89c590c34702ff80f32b13db6f67fa6f795dddd))
* **infra/readers:** add sqlite_query_reader.py reader infra module ([1c9eb8c](https://github.com/tks18/semantic-finance-etl/commit/1c9eb8c243f239d0e338e308076afa9a7e62e915))
* **infra/selector:** add latest_modifier_selector.py infra module ([5f55edc](https://github.com/tks18/semantic-finance-etl/commit/5f55edc0aff6606257ac4e06162a8121edae616c))


### Tests 🧪

* **tests/cases:** add config_service tester ([6a1d350](https://github.com/tks18/semantic-finance-etl/commit/6a1d350440fc20a30273254a15c545b5a531ae13))
* **tests/samples:** add sample db for test ([b2bc87c](https://github.com/tks18/semantic-finance-etl/commit/b2bc87c98ec1377ec1f8635f238eeca267b6c251))

### [0.1.1-6](https://github.com/tks18/semantic-finance-etl/compare/0.1.1-5...0.1.1-6) (2026-07-15)


### Tests 🧪

* **tests/cases:** add tests to test hooks import and registry ([5844429](https://github.com/tks18/semantic-finance-etl/commit/584442968cac9c203dc3d42c26c4d767da152525))
* **tests/samples:** add a simple transformation hook for testing ([992175c](https://github.com/tks18/semantic-finance-etl/commit/992175cae469e272fd59950e90f746312c77f49c))


### Features 🔥

* **contracts:** add source_discoverer.py contract ([ab971e1](https://github.com/tks18/semantic-finance-etl/commit/ab971e1185f16326d13a75aa4232515588bf2781))
* **contracts:** add source_grouper.py contract ([cf850e1](https://github.com/tks18/semantic-finance-etl/commit/cf850e1b50923436060895118203012a11175ddb))
* **contracts:** add source_selector.py contract ([ad2053a](https://github.com/tks18/semantic-finance-etl/commit/ad2053ae2a7cce3f7948989070e2cfa9c5573b5d))
* **contracts:** add sourcer_reader.py contract ([7a1c654](https://github.com/tks18/semantic-finance-etl/commit/7a1c6548999f86cd4e1330862c8e5f17648da0c7))
* **etl/hooks:** add hook_binding_resolver.py ([99ccd18](https://github.com/tks18/semantic-finance-etl/commit/99ccd18ed9f22b09efc00412360e5cfa90f8dfd3))
* **etl/hooks:** add hook_context_factory.py ([53a6ee7](https://github.com/tks18/semantic-finance-etl/commit/53a6ee7d9acf9fc847a052f41f60351578ab5437))
* **etl/hooks:** add hook_runner.py ([cbf40f1](https://github.com/tks18/semantic-finance-etl/commit/cbf40f1245123bab114db1cf2e7612542fc69087))
* **infra/plugins:** add hook_loader infra plugin ([c101015](https://github.com/tks18/semantic-finance-etl/commit/c10101579ab7beadc9796ba6c44ef448ecc6e75e))
* **infra/plugins:** add local_plugin_registry.py ([767249e](https://github.com/tks18/semantic-finance-etl/commit/767249eab13a27f0268a5b0166e7ef66611feece))

### [0.1.1-5](https://github.com/tks18/semantic-finance-etl/compare/0.1.1-4...0.1.1-5) (2026-07-15)


### Features 🔥

* **contracts:** add hooks.py for the hook definitions ([ef6ea46](https://github.com/tks18/semantic-finance-etl/commit/ef6ea468ed90aee220a905bbf24e87560eac2377))
* **domain/models:** add hook_results models ([8b85c28](https://github.com/tks18/semantic-finance-etl/commit/8b85c28eda3898150f631ca4c7c04cbf4d693d43))

### [0.1.1-4](https://github.com/tks18/semantic-finance-etl/compare/0.1.1-2...0.1.1-4) (2026-07-15)


### Features 🔥

* **config/services:** add project_config service ([3e907f8](https://github.com/tks18/semantic-finance-etl/commit/3e907f841eccd9ae71a89b15333a670a88947d8f))

### [0.1.1-3](https://github.com/tks18/semantic-finance-etl/compare/0.1.1-2...0.1.1-3) (2026-07-15)


### Features 🔥

* **config/services:** add project_config service ([3e907f8](https://github.com/tks18/semantic-finance-etl/commit/3e907f841eccd9ae71a89b15333a670a88947d8f))

### [0.1.1-2](https://github.com/tks18/semantic-finance-etl/compare/0.1.1-1...0.1.1-2) (2026-07-15)


### Features 🔥

* **config/loader:** add a project_loader utility module ([648b29c](https://github.com/tks18/semantic-finance-etl/commit/648b29cc9636c4adcca1e6dd1f57646b6b2660bb))
* **config/loader:** create a basic yaml_loader.py ([b241278](https://github.com/tks18/semantic-finance-etl/commit/b241278bd86c3b0bff402c1e468f4ce89eb985eb))
* **config/services:** add a config validation service ([f310b83](https://github.com/tks18/semantic-finance-etl/commit/f310b838dd19eba41195e42f3cbac31b8b739462))


### Tests 🧪

* **tests/config:** add a sample disparated configs for project, runtime, tables, sources ([f2f5103](https://github.com/tks18/semantic-finance-etl/commit/f2f5103553ad294353e7c1303afda6c79c8b4223))
* **tests/config:** test a simple project config parsing ([f5e72ae](https://github.com/tks18/semantic-finance-etl/commit/f5e72ae1d109fe4f0d5b2fb913ea6f801f78d837))

### [0.1.1-1](https://github.com/tks18/semantic-finance-etl/compare/0.1.1-0...0.1.1-1) (2026-07-15)


### Docs 📃

* add project_roadmap file ([f6d52ac](https://github.com/tks18/semantic-finance-etl/commit/f6d52ac73ed4097efae4b08d930493c73f86ae7f))
* **project_roadmap:** remove the document as its unnecessary, later a new briefing will be added ([8a3d249](https://github.com/tks18/semantic-finance-etl/commit/8a3d2497bf8bf55bc82a2bda926784a13ca98b41))
* update project roadmap ([db07fc2](https://github.com/tks18/semantic-finance-etl/commit/db07fc2531eccabb22d57c9059d7761d5ef75054))
* update project roadmap ([f302549](https://github.com/tks18/semantic-finance-etl/commit/f30254963a504ba5a6602f2f36d23551849a1f87))
* update project roadmap ([34381eb](https://github.com/tks18/semantic-finance-etl/commit/34381ebf658dff2f7667b27929925378353003fe))
* update project roadmap ([c9746a3](https://github.com/tks18/semantic-finance-etl/commit/c9746a3e079da33c15dcff1a6095f5e3c34f22d8))


### Build System 🏗

* **pyproject:** add pyyaml dependency ([0cb5788](https://github.com/tks18/semantic-finance-etl/commit/0cb578809ae7e58bdf8cfbc4488777fbfaa5d580))
* **pyproject:** update pyproject to reflect good build strategy ([cd78db4](https://github.com/tks18/semantic-finance-etl/commit/cd78db451c87c98ae8a7ee8f776fabaecef43de0))


### Features 🔥

* **config/models:** add project_config.py ([c615dd6](https://github.com/tks18/semantic-finance-etl/commit/c615dd67ad48fdc3ef81bddc8a2af5bb1044790c))
* **config/models:** add runtime_config.py ([f34cc14](https://github.com/tks18/semantic-finance-etl/commit/f34cc1401501540cca740512139fb187a9cb4503))
* **config/models:** add semantic_config.py ([52675e8](https://github.com/tks18/semantic-finance-etl/commit/52675e88fb8e7324e3cc59277b0059af17162334))
* **config/models:** add source_config.py ([31dde9c](https://github.com/tks18/semantic-finance-etl/commit/31dde9c21294232665d1a2b817c7e40f0b2a3aa9))
* **config/models:** add table_config.py ([d3075c8](https://github.com/tks18/semantic-finance-etl/commit/d3075c8a0dbc9a9edb1c53aac38be06c75f99d3c))
* **config/models:** add transform_config.py ([ae7c596](https://github.com/tks18/semantic-finance-etl/commit/ae7c5961907fda117792ee282e69980112f47ef3))
* **core:** add db_manager file ([6df7c9c](https://github.com/tks18/semantic-finance-etl/commit/6df7c9c699e79e9a5841ac597bd3ade57fc68321))
* **domain/enums:** add hookstage enums ([9922611](https://github.com/tks18/semantic-finance-etl/commit/9922611e80d599d609de341ab056b9ec2bc83c61))
* **domain:** add fail_behavior enums ([2dde74f](https://github.com/tks18/semantic-finance-etl/commit/2dde74f233e0bcc2e00b3cdf17326a0e462a357a))
* **domain:** add load_mode enums ([add322f](https://github.com/tks18/semantic-finance-etl/commit/add322f669bff4bae1e4c25ac4c639cee3e46f8c))
* **domain:** add table_kind enums ([b0d3915](https://github.com/tks18/semantic-finance-etl/commit/b0d3915979de79eb8b213707d7fb24bb0ec7d1bd))
* **root:** add main root entry point for the package ([4abcbef](https://github.com/tks18/semantic-finance-etl/commit/4abcbefdc1dabd545723074fd2cae24f9b3faf89))


### Tests 🧪

* **tests/samples:** add a sample config to test the existing functionality ([a79260e](https://github.com/tks18/semantic-finance-etl/commit/a79260e0e352dc8eb326df5a86e1af7b4f8f1c28))

### 0.1.1-0 (2026-07-11)


### Others 🔧

* **housekeeping:** add dev dependencies and update pyproject ([ffe42ea](https://github.com/tks18/semantic-finance-etl/commit/ffe42eaecec89c2645f4d4d51434d8ffed6fec78))
* initialize semantic-finance-etl python project ([69182ae](https://github.com/tks18/semantic-finance-etl/commit/69182ae7f89da921e44660d87ae90649c22dc624))
* **license:** add gpl-v3.0 license, update readme with the project roadmap ([3919b4b](https://github.com/tks18/semantic-finance-etl/commit/3919b4bb3ccdc9498b0c03d5166b25d0afce3179))


### CI 🛠

* **versionrc:** add versionrc for changelog mgmt & handling version bumping ([81e9c22](https://github.com/tks18/semantic-finance-etl/commit/81e9c22ed821a8e7d8d5ab90acb89b7c5f671817))
