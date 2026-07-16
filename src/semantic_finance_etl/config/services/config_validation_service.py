from __future__ import annotations

from semantic_finance_etl.config.models.project_config import ProjectConfig
from semantic_finance_etl.config.models.transform_config import StageHookBindings


class ConfigValidationService:
    def validate(self, config: ProjectConfig) -> None:
        errors: list[str] = []

        errors.extend(self._validate_unique_ids(config))
        errors.extend(self._validate_references(config))
        errors.extend(self._validate_hook_stage_placement(config))

        if errors:
            formatted_errors = "\n".join(f"- {error}" for error in errors)
            raise ValueError(f"Project configuration validation failed:\n{formatted_errors}")

    def _validate_unique_ids(self, config: ProjectConfig) -> list[str]:
        errors: list[str] = []

        source_ids = [source.source_id for source in config.sources]
        table_names = [table.table_name for table in config.tables]
        semantic_ids = [semantic.semantic_id for semantic in config.semantics]

        if len(source_ids) != len(set(source_ids)):
            errors.append("Duplicate source_id values found.")

        if len(table_names) != len(set(table_names)):
            errors.append("Duplicate table_name values found.")

        if len(semantic_ids) != len(set(semantic_ids)):
            errors.append("Duplicate semantic_id values found.")

        return errors

    def _validate_references(self, config: ProjectConfig) -> list[str]:
        errors: list[str] = []
        table_name_set = {table.table_name for table in config.tables}

        for source in config.sources:
            for target_table in source.target_tables:
                if target_table not in table_name_set:
                    errors.append(
                        f"Source '{source.source_id}' references missing target table "
                        f"'{target_table}'."
                    )

        for semantic in config.semantics:
            if semantic.source_table not in table_name_set:
                errors.append(
                    f"Semantic config '{semantic.semantic_id}' references missing source "
                    f"table '{semantic.source_table}'."
                )

        for table in config.tables:
            for dependency in table.depends_on:
                if dependency not in table_name_set:
                    errors.append(
                        f"Table '{table.table_name}' depends on missing table "
                        f"'{dependency}'."
                    )

        return errors

    def _validate_hook_stage_placement(self, config: ProjectConfig) -> list[str]:
        errors: list[str] = []

        source_allowed = {
            "post_read",
            "pre_append",
            "post_append",
            "pre_validate",
            "post_validate",
            "pre_load",
            "post_load",
        }

        table_allowed = {
            "post_append",
            "pre_validate",
            "post_validate",
            "pre_load",
            "post_load",
            "pre_derive",
            "post_derive",
        }

        semantic_allowed = {
            "pre_semantic",
            "post_semantic",
        }

        for source in config.sources:
            errors.extend(
                self._validate_stage_bindings(
                    owner_type="source",
                    owner_name=source.source_id,
                    hooks=source.hooks,
                    allowed_stages=source_allowed,
                )
            )

        for table in config.tables:
            allowed_stages = set(table_allowed)

            if table.table_kind.value != "derived":
                allowed_stages.discard("pre_derive")
                allowed_stages.discard("post_derive")

            errors.extend(
                self._validate_stage_bindings(
                    owner_type="table",
                    owner_name=table.table_name,
                    hooks=table.hooks,
                    allowed_stages=allowed_stages,
                )
            )

            if table.build is not None:
                errors.extend(
                    self._validate_stage_bindings(
                        owner_type="table_build",
                        owner_name=table.table_name,
                        hooks=table.build.hooks,
                        allowed_stages={"pre_derive", "post_derive"},
                    )
                )

        for semantic in config.semantics:
            errors.extend(
                self._validate_stage_bindings(
                    owner_type="semantic",
                    owner_name=semantic.semantic_id,
                    hooks=semantic.hooks,
                    allowed_stages=semantic_allowed,
                )
            )

        return errors

    def _validate_stage_bindings(
        self,
        owner_type: str,
        owner_name: str,
        hooks: StageHookBindings,
        allowed_stages: set[str],
    ) -> list[str]:
        errors: list[str] = []

        for stage_name, bindings in hooks.as_dict().items():
            if bindings and stage_name not in allowed_stages:
                errors.append(
                    f"{owner_type} '{owner_name}' uses hook stage '{stage_name}', "
                    f"which is not allowed in this config section."
                )

        return errors
