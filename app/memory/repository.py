import sqlite3
from contextlib import closing
from pathlib import Path
from uuid import uuid4


class MemoryRepository:
    """Guarda conversaciones, mensajes y memorias en SQLite.

    Es la única clase que conoce SQL. El router y los servicios
    solo llaman a sus métodos. Cada operación abre su propia
    conexión y las escrituras van dentro de una transacción.
    """

    def __init__(self, db_path: str) -> None:
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._create_tables()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=5)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _create_tables(self) -> None:
        with closing(self._connect()) as conn, conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL
                        REFERENCES conversations(id) ON DELETE CASCADE,
                    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_messages_conversation
                    ON messages(conversation_id, id);

                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL
                        REFERENCES conversations(id) ON DELETE CASCADE,
                    fact TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    # --- Conversaciones -------------------------------------------------

    def create_conversation(self) -> str:
        conversation_id = str(uuid4())
        with closing(self._connect()) as conn, conn:
            conn.execute("INSERT INTO conversations (id) VALUES (?)", (conversation_id,))
        return conversation_id

    def list_conversations(self) -> list[dict[str, str]]:
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT id, created_at FROM conversations ORDER BY created_at DESC, id"
            ).fetchall()
        return [{"conversation_id": cid, "created_at": created} for cid, created in rows]

    def conversation_exists(self, conversation_id: str) -> bool:
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT 1 FROM conversations WHERE id = ?", (conversation_id,)
            ).fetchone()
        return row is not None

    def delete_conversation(self, conversation_id: str) -> bool:
        with closing(self._connect()) as conn, conn:
            cursor = conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        return cursor.rowcount > 0

    # --- Mensajes -------------------------------------------------------

    def save_turn(self, conversation_id: str, question: str, answer: str) -> None:
        """Guarda la pregunta y la respuesta juntas: o se guardan ambas o ninguna."""
        with closing(self._connect()) as conn, conn:
            conn.executemany(
                "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
                [
                    (conversation_id, "user", question),
                    (conversation_id, "assistant", answer),
                ],
            )

    def list_messages(self, conversation_id: str, limit: int = 200) -> list[dict[str, str]]:
        """Devuelve los últimos `limit` mensajes de UNA conversación, del más antiguo al más nuevo."""
        with closing(self._connect()) as conn:
            rows = conn.execute(
                """
                SELECT role, content FROM messages
                WHERE conversation_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (conversation_id, limit),
            ).fetchall()
        return [{"role": role, "content": content} for role, content in reversed(rows)]

    # --- Memorias -------------------------------------------------------

    def add_memory(self, conversation_id: str, fact: str) -> dict[str, str]:
        memory_id = str(uuid4())
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "INSERT INTO memories (id, conversation_id, fact) VALUES (?, ?, ?)",
                (memory_id, conversation_id, fact),
            )
        return {"memory_id": memory_id, "fact": fact}

    def list_memories(self, conversation_id: str) -> list[dict[str, str]]:
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT id, fact FROM memories WHERE conversation_id = ? ORDER BY rowid",
                (conversation_id,),
            ).fetchall()
        return [{"memory_id": memory_id, "fact": fact} for memory_id, fact in rows]

    def delete_memory(self, conversation_id: str, memory_id: str) -> bool:
        with closing(self._connect()) as conn, conn:
            cursor = conn.execute(
                "DELETE FROM memories WHERE id = ? AND conversation_id = ?",
                (memory_id, conversation_id),
            )
        return cursor.rowcount > 0
