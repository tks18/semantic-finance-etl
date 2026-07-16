from __future__ import annotations

from pydantic import BaseModel, Field


class RuntimeConfig(BaseModel):
    local_db_path: str = "./data/app.db"
    log_level: str = "INFO"
    log_dir: str | None = None

    plugin_search_paths: list[str] = Field(default_factory=list)
    hook_search_paths: list[str] = Field(default_factory=list)

    fail_fast: bool = True
    parallelism: int = 1
    default_timeout_seconds: int = 300

    enable_semantic_indexing: bool = True
    dlq_table_name: str = "dead_letter_queue"
    run_metadata_retention_days: int = 90
