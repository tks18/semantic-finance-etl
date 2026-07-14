import sqlite3
import sqlite_vec
import logging
from typing import Any, Dict, List, Type, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Core Database Engine.
    Handles connections, performance PRAGMAs, and dynamic schema generation.
    """

    # Map Python/Pydantic types to SQLite STRICT types
    TYPE_MAP = {
        "int": "INTEGER",
        "float": "REAL",
        "str": "TEXT",
        "bool": "INTEGER",  # SQLite uses 1/0 for bools
        "datetime": "TEXT",
        "date": "TEXT",
        "bytes": "BLOB"
    }

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """Establishes connection, loads extensions, and applies performance PRAGMAs."""
        if self._conn is None:
            # check_same_thread=False allows our GUI thread and ETL thread to share it safely
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row

            # Load the sqlite-vec extension for AI vector search
            self._conn.enable_load_extension(True)
            sqlite_vec.load(self._conn)
            self._conn.enable_load_extension(False)

            self._apply_pragmas()
            logger.info(
                f"Connected to Sematic Finance DB at {self.db_path} with sqlite-vec loaded.")

        return self._conn

    def _apply_pragmas(self) -> None:
        """Applies high-performance settings for local SQLite."""
        if self._conn:
            cursor = self._conn.cursor()
            pragmas = [
                "PRAGMA journal_mode = WAL;",
                "PRAGMA synchronous = NORMAL;",
                "PRAGMA temp_store = MEMORY;",
                "PRAGMA foreign_keys = ON;"
            ]
            for pragma in pragmas:
                cursor.execute(pragma)
            self._conn.commit()

    def create_table_from_model(self, table_name: str, model: Type[BaseModel], primary_keys: List[str]) -> None:
        """
        Dynamically generates a SQLite STRICT table based on a Pydantic model.
        (Open/Closed Principle: Can accept any new table model without modifying this class).
        """
        if self._conn:
            columns = []
            for field_name, field_info in model.model_fields.items():
                py_type = field_info.annotation.__name__
                sql_type = self.TYPE_MAP.get(py_type, "TEXT")

                # Check if field is optional (nullable)
                is_nullable = type(None) in (
                    getattr(field_info.annotation, '__args__', []))
                null_constraint = "" if is_nullable else "NOT NULL"

                columns.append(f"{field_name} {sql_type} {null_constraint}")

            pk_constraint = f"PRIMARY KEY ({', '.join(primary_keys)})"
            columns.append(pk_constraint)

            # We use STRICT mode to ensure data integrity for future AI usage
            create_sql = f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    {', '.join(columns)}
                ) STRICT;
            """

            cursor = self.connect().cursor()
            cursor.execute(create_sql)
            self._conn.commit()
            logger.info(f"Verified schema for core table: {table_name}")

    def create_vector_table(self, table_name: str, vector_dim: int = 384) -> None:
        """Creates the vec0 shadow table for semantic embeddings."""
        if self._conn:
            vec_table_name = f"vec_{table_name}"
            create_sql = f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS {vec_table_name} USING vec0(
                    row_id TEXT PRIMARY KEY,
                    embedding float[{vector_dim}]
                );
            """
            cursor = self.connect().cursor()
            cursor.execute(create_sql)
            self._conn.commit()
            logger.info(f"Verified schema for vector table: {vec_table_name}")

    def close(self) -> None:
        """Safely closes the connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
