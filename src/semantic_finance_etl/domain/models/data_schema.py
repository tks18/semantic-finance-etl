from __future__ import annotations

from enum import StrEnum
from typing import Any, Iterable

import polars as pl
from pydantic import BaseModel, Field, model_validator


class LogicalType(StrEnum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    TIME = "time"
    JSON = "json"
    BINARY = "binary"

    def to_polars_dtype(
        self,
        *,
        precision: int | None = None,
        scale: int | None = None,
    ) -> pl.DataType:
        if self == LogicalType.STRING:
            return pl.Utf8
        if self == LogicalType.INTEGER:
            return pl.Int64
        if self == LogicalType.FLOAT:
            return pl.Float64
        if self == LogicalType.DECIMAL:
            return pl.Decimal(precision or 38, scale or 10)
        if self == LogicalType.BOOLEAN:
            return pl.Boolean
        if self == LogicalType.DATE:
            return pl.Date
        if self == LogicalType.DATETIME:
            return pl.Datetime
        if self == LogicalType.TIME:
            return pl.Time
        if self == LogicalType.JSON:
            return pl.Utf8
        if self == LogicalType.BINARY:
            return pl.Binary
        return pl.Utf8

    @classmethod
    def from_python_value(cls, value: Any) -> "LogicalType":
        if value is None:
            return cls.STRING
        if isinstance(value, bool):
            return cls.BOOLEAN
        if isinstance(value, int) and not isinstance(value, bool):
            return cls.INTEGER
        if isinstance(value, float):
            return cls.FLOAT
        return cls.STRING


class DataColumnSchema(BaseModel):
    name: str
    logical_type: LogicalType
    nullable: bool = True
    description: str | None = None
    aliases: list[str] = Field(default_factory=list)
    default_value: Any | None = None
    precision: int | None = None
    scale: int | None = None
    tags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_decimal_shape(self) -> "DataColumnSchema":
        if self.logical_type == LogicalType.DECIMAL:
            if self.precision is not None and self.precision <= 0:
                raise ValueError("Decimal precision must be > 0.")
            if self.scale is not None and self.scale < 0:
                raise ValueError("Decimal scale must be >= 0.")
            if (
                self.precision is not None
                and self.scale is not None
                and self.scale > self.precision
            ):
                raise ValueError("Decimal scale cannot exceed precision.")
        return self

    def normalized_name(self) -> str:
        return self.name.strip().lower()

    def matches(self, candidate: str) -> bool:
        normalized = candidate.strip().lower()
        if normalized == self.normalized_name():
            return True
        return normalized in {alias.strip().lower() for alias in self.aliases}

    def to_polars_dtype(self) -> pl.DataType:
        return self.logical_type.to_polars_dtype(
            precision=self.precision,
            scale=self.scale,
        )

    def is_compatible_with(
        self,
        other: "DataColumnSchema",
        *,
        strict_nullability: bool = False,
    ) -> bool:
        if self.normalized_name() != other.normalized_name():
            return False
        if self.logical_type != other.logical_type:
            return False
        if strict_nullability and self.nullable != other.nullable:
            return False
        return True


class SchemaTypeMismatch(BaseModel):
    column_name: str
    expected_type: LogicalType
    actual_type: LogicalType


class SchemaNullabilityMismatch(BaseModel):
    column_name: str
    expected_nullable: bool
    actual_nullable: bool


class DataSchemaDiff(BaseModel):
    missing_in_left: list[str] = Field(default_factory=list)
    missing_in_right: list[str] = Field(default_factory=list)
    type_mismatches: list[SchemaTypeMismatch] = Field(default_factory=list)
    nullability_mismatches: list[SchemaNullabilityMismatch] = Field(default_factory=list)

    def is_empty(self) -> bool:
        return not (
            self.missing_in_left
            or self.missing_in_right
            or self.type_mismatches
            or self.nullability_mismatches
        )


class DataSchema(BaseModel):
    columns: list[DataColumnSchema]
    primary_key: list[str] = Field(default_factory=list)
    description: str | None = None

    @model_validator(mode="after")
    def validate_unique_columns(self) -> "DataSchema":
        seen: set[str] = set()
        duplicates: list[str] = []

        for column in self.columns:
            normalized = column.normalized_name()
            if normalized in seen:
                duplicates.append(column.name)
            seen.add(normalized)

        if duplicates:
            raise ValueError(f"Duplicate schema columns found: {duplicates}")

        missing_pk = [
            pk for pk in self.primary_key if pk.strip().lower() not in seen
        ]
        if missing_pk:
            raise ValueError(
                f"Primary key columns not present in schema: {missing_pk}"
            )

        return self

    @property
    def column_names(self) -> list[str]:
        return [column.name for column in self.columns]

    def normalized_column_names(self) -> list[str]:
        return [column.normalized_name() for column in self.columns]

    def has_column(self, name: str) -> bool:
        return self.get_column(name) is not None

    def get_column(self, name: str) -> DataColumnSchema | None:
        normalized = name.strip().lower()
        for column in self.columns:
            if column.matches(normalized):
                return column
        return None

    def require_columns(self, names: Iterable[str]) -> None:
        missing = [name for name in names if not self.has_column(name)]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

    def to_polars_schema(self) -> dict[str, pl.DataType]:
        return {
            column.name: column.to_polars_dtype()
            for column in self.columns
        }

    def empty_lazyframe(self) -> pl.LazyFrame:
        return pl.DataFrame(schema=self.to_polars_schema()).lazy()

    def compare_to(
        self,
        other: "DataSchema",
        *,
        strict_nullability: bool = False,
    ) -> DataSchemaDiff:
        left_map = {column.normalized_name(): column for column in self.columns}
        right_map = {column.normalized_name(): column for column in other.columns}

        diff = DataSchemaDiff(
            missing_in_left=sorted(
                right.name
                for key, right in right_map.items()
                if key not in left_map
            ),
            missing_in_right=sorted(
                left.name
                for key, left in left_map.items()
                if key not in right_map
            ),
        )

        overlapping = set(left_map).intersection(right_map)
        for key in sorted(overlapping):
            left_col = left_map[key]
            right_col = right_map[key]

            if left_col.logical_type != right_col.logical_type:
                diff.type_mismatches.append(
                    SchemaTypeMismatch(
                        column_name=left_col.name,
                        expected_type=left_col.logical_type,
                        actual_type=right_col.logical_type,
                    )
                )

            if strict_nullability and left_col.nullable != right_col.nullable:
                diff.nullability_mismatches.append(
                    SchemaNullabilityMismatch(
                        column_name=left_col.name,
                        expected_nullable=left_col.nullable,
                        actual_nullable=right_col.nullable,
                    )
                )

        return diff

    @classmethod
    def from_mapping(
        cls,
        mapping: dict[str, LogicalType | str],
        *,
        nullable: bool = True,
    ) -> "DataSchema":
        columns = [
            DataColumnSchema(
                name=name,
                logical_type=(
                    logical_type
                    if isinstance(logical_type, LogicalType)
                    else LogicalType(logical_type)
                ),
                nullable=nullable,
            )
            for name, logical_type in mapping.items()
        ]
        return cls(columns=columns)

    @classmethod
    def infer_from_polars_schema(
        cls,
        schema: dict[str, pl.DataType],
    ) -> "DataSchema":
        def map_dtype(dtype: pl.DataType) -> LogicalType:
            if dtype in (pl.Int8, pl.Int16, pl.Int32, pl.Int64):
                return LogicalType.INTEGER
            if dtype in (pl.Float32, pl.Float64):
                return LogicalType.FLOAT
            if dtype == pl.Boolean:
                return LogicalType.BOOLEAN
            if dtype == pl.Date:
                return LogicalType.DATE
            if dtype == pl.Datetime:
                return LogicalType.DATETIME
            if dtype == pl.Time:
                return LogicalType.TIME
            if dtype == pl.Binary:
                return LogicalType.BINARY
            if isinstance(dtype, pl.Decimal):
                return LogicalType.DECIMAL
            return LogicalType.STRING

        return cls(
            columns=[
                DataColumnSchema(
                    name=name,
                    logical_type=map_dtype(dtype),
                    nullable=True,
                )
                for name, dtype in schema.items()
            ]
        )
