# Changelog

All notable changes to this project will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

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
