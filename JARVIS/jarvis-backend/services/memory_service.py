import re
import sqlite3
from pathlib import Path
from typing import List, Dict


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

        connection = sqlite3.connect(self.database_path)
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT NOT NULL DEFAULT 'active'
                )
                """
            )

            # Safely migrate databases created before status existed.
            columns = {
                row["name"]
                for row in connection.execute(
                    "PRAGMA table_info(memories)"
                ).fetchall()
            }

            if "status" not in columns:
                connection.execute(
                    """
                    ALTER TABLE memories
                    ADD COLUMN status TEXT NOT NULL DEFAULT 'active'
                    """
                )

            connection.commit()

        # -----------------------------------------------------
    # FIND DUPLICATE MEMORY
    # -----------------------------------------------------

    def find_duplicate_memory(
        self,
        memory: str
    ) -> Optional[Dict]:

        def normalize(text):
            text = text.lower().strip()
            text = re.sub(r"[^\w\s]", "", text)
            return " ".join(text.split())

        normalized_memory = normalize(memory)

        with self.get_connection() as connection:

            rows = connection.execute(
                """
                SELECT id, memory, category, created_at, status
                FROM memories
                WHERE status = 'active'
                """
            ).fetchall()

            for row in rows:

                existing = dict(row)

                if normalize(existing["memory"]) == normalized_memory:
                    return existing

        return None

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
                INSERT INTO memories (memory, category, status)
                VALUES (?, ?, 'active')
                """,
                (memory, category)
            )

            connection.commit()

            return cursor.lastrowid

    # -----------------------------------------------------
    # GET MEMORIES
    # -----------------------------------------------------

    def get_all_memories(
        self,
        include_inactive: bool = False
    ) -> List[Dict]:

        query = """
            SELECT id, memory, category, created_at, status
            FROM memories
        """

        if not include_inactive:
            query += " WHERE status = 'active'"

        query += " ORDER BY created_at DESC"

        with self.get_connection() as connection:

            rows = connection.execute(query).fetchall()

            return [dict(row) for row in rows]

    # -----------------------------------------------------
    # SEARCH MEMORIES
    # -----------------------------------------------------

    def search_memories(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict]:

        keywords = re.findall(
            r"\b[a-zA-Z0-9]+\b",
            query.lower()
        )

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
            word for word in keywords
            if len(word) > 2 and word not in stop_words
        ]

        if not keywords:
            return []

        conditions = []
        parameters = []

        for keyword in keywords:
            conditions.append("LOWER(memory) LIKE ?")
            parameters.append(f"%{keyword}%")

        sql = f"""
            SELECT id, memory, category, created_at, status
            FROM memories
            WHERE status = 'active'
            AND ({" OR ".join(conditions)})
            ORDER BY created_at DESC
            LIMIT ?
        """

        parameters.append(limit)

        with self.get_connection() as connection:

            rows = connection.execute(
                sql,
                parameters
            ).fetchall()

            return [dict(row) for row in rows]

    # -----------------------------------------------------
    # SUPERSEDE MEMORIES
    # -----------------------------------------------------

    def supersede_memories(
        self,
        memory_ids: List[int]
    ) -> int:

        if not memory_ids:
            return 0

        placeholders = ",".join("?" for _ in memory_ids)

        with self.get_connection() as connection:

            cursor = connection.execute(
                f"""
                UPDATE memories
                SET status = 'superseded'
                WHERE id IN ({placeholders})
                AND status = 'active'
                """,
                memory_ids
            )

            connection.commit()

            return cursor.rowcount

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