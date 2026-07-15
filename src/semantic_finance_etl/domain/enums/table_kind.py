from enum import StrEnum


class TableKind(StrEnum):
    CANONICAL = "canonical"
    DERIVED = "derived"
    SYSTEM = "system"
