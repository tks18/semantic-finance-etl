from enum import StrEnum


class FailBehavior(StrEnum):
    FAIL_RUN = "fail_run"
    SKIP_HOOK = "skip_hook"
    WARN_ONLY = "warn_only"
    ROUTE_TO_DLQ = "route_to_dlq"
