from enum import StrEnum


class LoadMode(StrEnum):
    APPEND = "append"
    UPSERT = "upsert"
    REPLACE = "replace"
