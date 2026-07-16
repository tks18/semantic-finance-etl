from __future__ import annotations

from dataclasses import dataclass, field

from semantic_finance_etl.config.models.semantic_config import ChunkingConfig
from semantic_finance_etl.semantic.projection_service import SemanticDocument


@dataclass(slots=True)
class DocumentChunk:
    """A single chunk of a semantic document."""

    chunk_id: str
    doc_id: str
    semantic_id: str
    source_table: str
    source_pk: str | None
    chunk_index: int
    chunk_text: str
    title: str | None
    metadata: dict
    tags: list[str]

    @property
    def char_count(self) -> int:
        return len(self.chunk_text)


@dataclass(slots=True)
class ChunkingResult:
    """Summary of a chunking operation over a set of documents."""

    semantic_id: str
    chunks: list[DocumentChunk] = field(default_factory=list)
    total_documents: int = 0
    total_chunks: int = 0


class ChunkingService:
    """Splits semantic documents into fixed-size overlapping text chunks.

    Chunking is purely CPU-bound text splitting — no I/O, no LazyFrame.
    Each ``SemanticDocument.body`` is split into ``chunk_size``-character
    windows with ``chunk_overlap`` characters of overlap between consecutive
    chunks.

    Chunk IDs are derived as ``{doc_id}_{chunk_index}`` for deterministic
    tracing back to the source document.
    """

    def chunk_documents(
        self,
        documents: list[SemanticDocument],
        chunking_config: ChunkingConfig,
    ) -> ChunkingResult:
        """Chunk a list of semantic documents.

        Parameters
        ----------
        documents:
            Projected documents from ``ProjectionService.project()``.
        chunking_config:
            ``ChunkingConfig`` from ``SemanticConfig`` specifying
            ``chunk_size`` and ``chunk_overlap``.

        Returns
        -------
        ChunkingResult
            All produced chunks plus aggregate counts.
        """
        result = ChunkingResult(
            semantic_id=documents[0].semantic_id if documents else "",
            total_documents=len(documents),
        )

        for doc in documents:
            chunks = self._chunk_document(doc, chunking_config)
            result.chunks.extend(chunks)

        result.total_chunks = len(result.chunks)
        return result

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _chunk_document(
        self,
        doc: SemanticDocument,
        cfg: ChunkingConfig,
    ) -> list[DocumentChunk]:
        text = doc.body
        size = cfg.chunk_size
        overlap = cfg.chunk_overlap
        step = max(size - overlap, 1)

        chunks: list[DocumentChunk] = []
        start = 0
        idx = 0

        while start < len(text):
            chunk_text = text[start : start + size]
            chunk_id = f"{doc.doc_id}_{idx}"

            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    doc_id=doc.doc_id,
                    semantic_id=doc.semantic_id,
                    source_table=doc.source_table,
                    source_pk=doc.source_pk,
                    chunk_index=idx,
                    chunk_text=chunk_text,
                    title=doc.title,
                    metadata=doc.metadata,
                    tags=doc.tags,
                )
            )

            start += step
            idx += 1

            if not chunk_text:
                break

        # Guarantee at least one chunk even for an empty body.
        if not chunks:
            chunks.append(
                DocumentChunk(
                    chunk_id=f"{doc.doc_id}_0",
                    doc_id=doc.doc_id,
                    semantic_id=doc.semantic_id,
                    source_table=doc.source_table,
                    source_pk=doc.source_pk,
                    chunk_index=0,
                    chunk_text="",
                    title=doc.title,
                    metadata=doc.metadata,
                    tags=doc.tags,
                )
            )

        return chunks
