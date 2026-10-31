import re
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional


# ---------------------------------------------------------
# DATABASE
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(exist_ok=True)

DATABASE_PATH = DATA_DIR / "jarvis_memory.db"


# ---------------------------------------------------------
# MEMORY SERVICE
# ---------------------------------------------------------

class MemoryService:

    def __init__(self):
        self.database_path = DATABASE_PATH
        self.initialize_database()


    # -----------------------------------------------------
    # DATABASE CONNECTION
    # -----------------------------------------------------

    def get_connection(self):

        connection = sqlite3.connect(
            self.database_path
        )

        connection.row_factory = sqlite3.Row

        return connection


    # -----------------------------------------------------
    # INITIALIZE DATABASE
    # -----------------------------------------------------

    def initialize_database(self):

        with self.get_connection() as connection:

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    memory TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            connection.commit()


    # -----------------------------------------------------
    # SAVE MEMORY
    # -----------------------------------------------------

    def save_memory(
        self,
        memory: str,
        category: str = "general"
    ) -> int:

        with self.get_connection() as connection:

            cursor = connection.execute(
                """
                INSERT INTO memories (
                    memory,
                    category
                )
                VALUES (?, ?)
                """,
                (
                    memory,
                    category
                )
            )

            connection.commit()

            return cursor.lastrowid


    # -----------------------------------------------------
    # GET ALL MEMORIES
    # -----------------------------------------------------

    def get_all_memories(self) -> List[Dict]:

        with self.get_connection() as connection:

            rows = connection.execute(
                """
                SELECT
                    id,
                    memory,
                    category,
                    created_at
                FROM memories
                ORDER BY created_at DESC
                """
            ).fetchall()

            return [
                dict(row)
                for row in rows
            ]


    # -----------------------------------------------------
    # SEARCH MEMORIES
    # -----------------------------------------------------

    def search_memories(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict]:

        # Extract words while removing punctuation
        keywords = re.findall(
            r"\b[a-zA-Z0-9]+\b",
            query.lower()
        )

        # Ignore short, insignificant words
        stop_words = {
            "what", "who", "where", "when",
            "why", "how", "the", "and",
            "for", "are", "was", "were",
            "you", "your", "with", "from",
            "that", "this", "have", "does",
            "did", "can", "could", "would",
            "should", "about"
        }

        keywords = [
            word
            for word in keywords
            if len(word) > 2 and word not in stop_words
        ]

        if not keywords:
            return []

        conditions = []
        parameters = []

        for keyword in keywords:

            conditions.append(
                "LOWER(memory) LIKE ?"
            )

            parameters.append(
                f"%{keyword}%"
            )

        sql = f"""
            SELECT
                id,
                memory,
                category,
                created_at
            FROM memories
            WHERE {" OR ".join(conditions)}
            ORDER BY created_at DESC
            LIMIT ?
        """

        parameters.append(limit)

        with self.get_connection() as connection:

            rows = connection.execute(
                sql,
                parameters
            ).fetchall()

            return [
                dict(row)
                for row in rows
            ]

    # -----------------------------------------------------
    # DELETE MEMORY
    # -----------------------------------------------------

    def delete_memory(
        self,
        memory_id: int
    ) -> bool:

        with self.get_connection() as connection:

            cursor = connection.execute(
                """
                DELETE FROM memories
                WHERE id = ?
                """,
                (memory_id,)
            )

            connection.commit()

            return cursor.rowcount > 0