from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

import polars as pl

from semantic_finance_etl.config.models.semantic_config import (
    ProjectionConfig,
    SemanticConfig,
)


@dataclass(slots=True)
class SemanticDocument:
    """A single projected semantic document ready for chunking and indexing."""

    doc_id: str
    source_table: str
    source_pk: str | None
    semantic_id: str
    title: str | None
    body: str
    metadata: dict[str, Any]
    tags: list[str]
    source_row_index: int


@dataclass(slots=True)
class ProjectionResult:
    """Summary of a projection operation."""

    semantic_id: str
    source_table: str
    documents: list[SemanticDocument] = field(default_factory=list)
    skipped_rows: int = 0
    error: str | None = None

    @property
    def document_count(self) -> int:
        return len(self.documents)


class ProjectionService:
    """Projects structured table rows into semantic documents.

    The projection operates on a ``pl.LazyFrame`` — data is collected here
    at the document generation boundary (the only collection point in the
    semantic layer prior to chunking/indexing).

    Template rendering uses Python ``.format_map()`` so config-defined
    templates like ``"Company: {company_name}, Value: {revenue}"`` resolve
    directly from each row's field values.
    """

    def project(
        self,
        *,
        lazy_frame: pl.LazyFrame,
        semantic_config: SemanticConfig,
    ) -> ProjectionResult:
        """Project all rows from ``lazy_frame`` into semantic documents.

        Parameters
        ----------
        lazy_frame:
            The source table data as a Polars ``LazyFrame``.
        semantic_config:
            Configuration declaring projection template, metadata fields, etc.

        Returns
        -------
        ProjectionResult
            All generated documents plus skipped-row count.
        """
        result = ProjectionResult(
            semantic_id=semantic_config.semantic_id,
            source_table=semantic_config.source_table,
        )

        # --- Explicit collect boundary for semantic projection ---
        df: pl.DataFrame = lazy_frame.collect()

        for i, row in enumerate(df.to_dicts()):
            try:
                doc = self._project_row(
                    row=row,
                    row_index=i,
                    semantic_config=semantic_config,
                )
                result.documents.append(doc)
            except Exception:
                result.skipped_rows += 1

        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _project_row(
        self,
        row: dict[str, Any],
        row_index: int,
        semantic_config: SemanticConfig,
    ) -> SemanticDocument:
        projection = semantic_config.projection

        title = self._render_template(
            projection.title_template, row
        ) if projection.title_template else None

        body = self._render_template(projection.body_template, row)

        metadata = {
            field_name: row.get(field_name)
            for field_name in projection.metadata_fields
        }
        metadata.update(semantic_config.extra_metadata)

        tags = [
            str(row.get(field_name, ""))
            for field_name in projection.tag_fields
            if row.get(field_name) is not None
        ]

        doc_id = self._make_doc_id(
            strategy=semantic_config.document_id_strategy,
            semantic_id=semantic_config.semantic_id,
            row=row,
            row_index=row_index,
        )

        source_pk = None
        if semantic_config.source_pk_field:
            val = row.get(semantic_config.source_pk_field)
            if val is not None:
                source_pk = str(val)

        return SemanticDocument(
            doc_id=doc_id,
            source_table=semantic_config.source_table,
            source_pk=source_pk,
            semantic_id=semantic_config.semantic_id,
            title=title,
            body=body,
            metadata=metadata,
            tags=tags,
            source_row_index=row_index,
        )

    def _render_template(self, template: str, row: dict[str, Any]) -> str:
        """Render a Python format-map template against a row dict.

        Missing keys produce an empty string rather than a ``KeyError``.
        """
        safe_row = _SafeDict(row)
        return template.format_map(safe_row)

    def _make_doc_id(
        self,
        strategy: str,
        semantic_id: str,
        row: dict[str, Any],
        row_index: int,
    ) -> str:
        if strategy == "deterministic_hash":
            content = f"{semantic_id}::{sorted(row.items())}"
            return hashlib.sha256(content.encode()).hexdigest()[:32]

        if strategy == "row_index":
            return f"{semantic_id}_{row_index}"

        # Fallback — deterministic hash
        content = f"{semantic_id}::{sorted(row.items())}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]


class _SafeDict(dict):
    """A dict subclass that returns empty string for missing keys in format_map."""

    def __missing__(self, key: str) -> str:
        return ""
