import json
import sqlite3
import os


DRIVE_DB_PATH = (
    "/content/drive/MyDrive/"
    "AdviserAI/data/adviser.db"
)

LOCAL_DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data",
    "adviser.db"
)


def get_db_path():
    configured_path = os.environ.get("DB_PATH", "").strip()

    if configured_path:
        db_path = configured_path
    elif os.path.isdir("/content/drive/MyDrive"):
        db_path = DRIVE_DB_PATH
    else:
        db_path = LOCAL_DB_PATH

    db_path = os.path.abspath(db_path)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    return db_path


def get_connection():
    return sqlite3.connect(get_db_path())


def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                memory TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, memory)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                file_name TEXT,
                adviser_mind TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, file_hash)
            )
        """)

        # Migration for databases created
        # before searchable chunks were persisted.
        columns = {
            row[1]
            for row in conn.execute(
                "PRAGMA table_info(user_knowledge)"
            ).fetchall()
        }

        if "chunks_json" not in columns:
            conn.execute(
                """
                ALTER TABLE user_knowledge
                ADD COLUMN chunks_json TEXT
                """
            )


def save_memory(user_id, memory):
    if not memory:
        return

    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO memories
            (user_id, memory)
            VALUES (?, ?)
            """,
            (user_id, memory)
        )


def load_memories(user_id):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT memory
            FROM memories
            WHERE user_id = ?
            ORDER BY id
            """,
            (user_id,)
        ).fetchall()

    return [row[0] for row in rows]


def replace_memory(
    user_id,
    old_memory,
    new_memory
):
    with get_connection() as conn:
        conn.execute(
            """
            DELETE FROM memories
            WHERE user_id = ?
            AND memory = ?
            """,
            (user_id, old_memory)
        )

        if new_memory:
            conn.execute(
                """
                INSERT OR IGNORE INTO memories
                (user_id, memory)
                VALUES (?, ?)
                """,
                (user_id, new_memory)
            )


def delete_memory(user_id, memory):
    with get_connection() as conn:
        conn.execute(
            """
            DELETE FROM memories
            WHERE user_id = ?
            AND memory = ?
            """,
            (user_id, memory)
        )

def create_user(
    user_id,
    username,
    password_hash
):
    user_id = str(user_id).strip()
    username = str(username).strip().lower()
    password_hash = str(password_hash).strip()

    if not user_id:
        raise ValueError("user_id is required.")

    if not username:
        raise ValueError("username is required.")

    if not password_hash:
        raise ValueError("password_hash is required.")

    try:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO users (
                    id,
                    username,
                    password_hash
                )
                VALUES (?, ?, ?)
                """,
                (
                    user_id,
                    username,
                    password_hash
                )
            )

        return True

    except sqlite3.IntegrityError:
        return False


def get_user_by_username(username):
    username = str(username).strip().lower()

    if not username:
        return None

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT
                id,
                username,
                password_hash,
                created_at
            FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()

    if row is None:
        return None

    return {
        "id": row[0],
        "username": row[1],
        "password_hash": row[2],
        "created_at": row[3]
    }


def delete_user(user_id):
    user_id = str(user_id).strip()

    with get_connection() as conn:
        conn.execute(
            """
            DELETE FROM users
            WHERE id = ?
            """,
            (user_id,)
        )

def save_user_knowledge(
    user_id,
    file_hash,
    file_name,
    adviser_mind,
    chunks=None
):
    user_id = str(user_id).strip()
    file_hash = str(file_hash).strip()
    file_name = str(file_name or "").strip()
    adviser_mind = str(adviser_mind).strip()

    if not user_id:
        raise ValueError("user_id is required.")

    if not file_hash:
        raise ValueError("file_hash is required.")

    if not adviser_mind:
        raise ValueError("adviser_mind is required.")

    chunks_json = json.dumps(
        chunks or [],
        ensure_ascii=False
    )

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO user_knowledge (
                user_id,
                file_hash,
                file_name,
                adviser_mind,
                chunks_json
            )
            VALUES (?, ?, ?, ?, ?)

            ON CONFLICT(user_id, file_hash)
            DO UPDATE SET
                file_name = excluded.file_name,
                adviser_mind = excluded.adviser_mind,
                chunks_json = excluded.chunks_json
            """,
            (
                user_id,
                file_hash,
                file_name,
                adviser_mind,
                chunks_json
            )
        )

    return True


def load_user_knowledge(user_id):
    user_id = str(user_id).strip()

    if not user_id:
        return []

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                file_hash,
                file_name,
                adviser_mind,
                chunks_json,
                created_at
            FROM user_knowledge
            WHERE user_id = ?
            ORDER BY created_at ASC
            """,
            (user_id,)
        ).fetchall()

    records = []

    for row in rows:
        try:
            chunks = json.loads(
                row[3] or "[]"
            )
        except (json.JSONDecodeError, TypeError):
            chunks = []

        records.append({
            "file_hash": row[0],
            "file_name": row[1],
            "adviser_mind": row[2],
            "chunks": chunks,
            "created_at": row[4]
        })

    return records


def delete_user_knowledge(
    user_id,
    file_hash
):
    user_id = str(user_id).strip()
    file_hash = str(file_hash).strip()

    with get_connection() as conn:
        conn.execute(
            """
            DELETE FROM user_knowledge
            WHERE user_id = ?
              AND file_hash = ?
            """,
            (
                user_id,
                file_hash
            )
        )

