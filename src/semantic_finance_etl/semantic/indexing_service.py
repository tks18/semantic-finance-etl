from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from semantic_finance_etl.semantic.chunking_service import DocumentChunk


SEMANTIC_INDEX_TABLE = "etl_semantic_index"
SEMANTIC_VECTORS_TABLE = "etl_semantic_vectors"

SEMANTIC_INDEX_DDL = f"""
CREATE TABLE IF NOT EXISTS {SEMANTIC_INDEX_TABLE} (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    chunk_id        TEXT    UNIQUE NOT NULL,
    doc_id          TEXT    NOT NULL,
    semantic_id     TEXT    NOT NULL,
    source_table    TEXT    NOT NULL,
    source_pk       TEXT,
    chunk_index     INTEGER NOT NULL,
    chunk_text      TEXT    NOT NULL,
    title           TEXT,
    metadata_json   TEXT,
    tags_json       TEXT,
    char_count      INTEGER,
    run_id          TEXT,
    indexed_at      TEXT    NOT NULL
)
"""


@dataclass(slots=True)
class IndexingResult:
    """Summary of one indexing operation."""

    semantic_id: str
    run_id: str
    indexed_chunks: int = 0
    replaced_chunks: int = 0
    error: str | None = None


class IndexingService:
    """Persists semantic document chunks into the SQLite semantic index.

    The index table (``etl_semantic_index``) stores every chunk with its
    text, metadata, and provenance so downstream search and retrieval can
    query over it.

    Future extension point: an embedding service can be layered on top by
    adding an ``embedding_vector`` column (BLOB) and calling an embedding
    model per chunk before calling ``index_chunks()``.
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_index_table()

    def index_chunks(
        self,
        chunks: list[DocumentChunk],
        *,
        run_id: str,
        replace_existing: bool = True,
    ) -> IndexingResult:
        """Persist chunks into the semantic index table.

        Parameters
        ----------
        chunks:
            Chunks from ``ChunkingService.chunk_documents()``.
        run_id:
            ETL run ID for provenance tracking.
        replace_existing:
            When ``True``, existing rows with the same ``chunk_id`` are
            replaced (UPSERT).  When ``False``, existing rows are skipped.
        """
        if not chunks:
            return IndexingResult(
                semantic_id="",
                run_id=run_id,
                indexed_chunks=0,
            )

        semantic_id = chunks[0].semantic_id
        result = IndexingResult(semantic_id=semantic_id, run_id=run_id)

        try:
            now = datetime.now(timezone.utc).isoformat()
            self._write_chunks(
                chunks=chunks,
                run_id=run_id,
                indexed_at=now,
                replace_existing=replace_existing,
                result=result,
            )
        except Exception as exc:
            import traceback
            traceback.print_exc()
            result.error = f"{type(exc).__name__}: {exc}"

        return result

    def query_chunks(
        self,
        *,
        semantic_id: str | None = None,
        source_table: str | None = None,
        run_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Query indexed chunks with optional filters."""
        conditions: list[str] = []
        params: list[Any] = []

        if semantic_id is not None:
            conditions.append("semantic_id = ?")
            params.append(semantic_id)
        if source_table is not None:
            conditions.append("source_table = ?")
            params.append(source_table)
        if run_id is not None:
            conditions.append("run_id = ?")
            params.append(run_id)

        where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        sql = f"SELECT * FROM {SEMANTIC_INDEX_TABLE} {where_clause} ORDER BY semantic_id, doc_id, chunk_index LIMIT ?"
        params.append(limit)

        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_chunk(self, chunk_id: str) -> dict[str, Any] | None:
        """Retrieve a single chunk by ID."""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {SEMANTIC_INDEX_TABLE} WHERE chunk_id = ?",
                (chunk_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def delete_chunks_for_semantic(self, semantic_id: str) -> int:
        """Delete all chunks for a given semantic config ID. Returns count deleted."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                f"DELETE FROM {SEMANTIC_INDEX_TABLE} WHERE semantic_id = ?",
                (semantic_id,),
            )
            deleted = cursor.rowcount
            conn.commit()
            return deleted
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _get_connection(self) -> sqlite3.Connection:
        import sqlite_vec
        conn = sqlite3.connect(str(self._db_path))
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        return conn

    def _ensure_index_table(self) -> None:
        conn = self._get_connection()
        try:
            conn.execute(SEMANTIC_INDEX_DDL)
            conn.execute(f"CREATE VIRTUAL TABLE IF NOT EXISTS {SEMANTIC_VECTORS_TABLE} USING vec0(id INTEGER PRIMARY KEY, source_row_id TEXT, embedding float[384])")
            
            conn.execute(f"""
            CREATE TRIGGER IF NOT EXISTS trg_delete_vec
            AFTER DELETE ON {SEMANTIC_INDEX_TABLE}
            BEGIN
                DELETE FROM {SEMANTIC_VECTORS_TABLE} WHERE id = old.id;
            END;
            """)
            conn.commit()
        finally:
            conn.close()

    def _write_chunks(
        self,
        chunks: list[DocumentChunk],
        run_id: str,
        indexed_at: str,
        replace_existing: bool,
        result: IndexingResult,
    ) -> None:
        if replace_existing:
            conflict_clause = """
            ON CONFLICT(chunk_id) DO UPDATE SET
                doc_id=excluded.doc_id,
                semantic_id=excluded.semantic_id,
                source_table=excluded.source_table,
                source_pk=excluded.source_pk,
                chunk_index=excluded.chunk_index,
                chunk_text=excluded.chunk_text,
                title=excluded.title,
                metadata_json=excluded.metadata_json,
                tags_json=excluded.tags_json,
                char_count=excluded.char_count,
                run_id=excluded.run_id,
                indexed_at=excluded.indexed_at
            """
        else:
            conflict_clause = "ON CONFLICT(chunk_id) DO NOTHING"

        sql = f"""
        INSERT INTO {SEMANTIC_INDEX_TABLE}
            (chunk_id, doc_id, semantic_id, source_table, source_pk, chunk_index,
             chunk_text, title, metadata_json, tags_json, char_count, run_id, indexed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        {conflict_clause}
        """

        values = [
            (
                chunk.chunk_id,
                chunk.doc_id,
                chunk.semantic_id,
                chunk.source_table,
                chunk.source_pk,
                chunk.chunk_index,
                chunk.chunk_text,
                chunk.title,
                json.dumps(chunk.metadata, default=str),
                json.dumps(chunk.tags),
                chunk.char_count,
                run_id,
                indexed_at,
            )
            for chunk in chunks
        ]

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # --- Delta Sync: Delete obsolete chunks ---
            semantic_id = chunks[0].semantic_id
            cursor.execute(f"SELECT chunk_id FROM {SEMANTIC_INDEX_TABLE} WHERE semantic_id = ?", (semantic_id,))
            existing_chunk_ids = {r[0] for r in cursor.fetchall()}
            
            new_chunk_ids = {chunk.chunk_id for chunk in chunks}
            obsolete_chunk_ids = existing_chunk_ids - new_chunk_ids
            
            if obsolete_chunk_ids:
                obs_list = list(obsolete_chunk_ids)
                batch_size = 900
                for i in range(0, len(obs_list), batch_size):
                    batch = obs_list[i:i+batch_size]
                    placeholders = ",".join(["?"] * len(batch))
                    cursor.execute(
                        f"DELETE FROM {SEMANTIC_INDEX_TABLE} WHERE chunk_id IN ({placeholders})",
                        batch
                    )
                    
            # Insert / Update new chunks ---
            conn.executemany(sql, values)
            
            conn.commit()
            result.indexed_chunks = len(chunks)
        finally:
            conn.close()
