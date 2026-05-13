"""Database layer — SQLite (default) or PostgreSQL (via DATABASE_URL)."""

import sqlite3
from datetime import datetime, timezone

from server.config import DATABASE_URL, DB_PATH, DEFAULT_SUBMOLTS

SCHEMA = """
CREATE TABLE IF NOT EXISTS agents (
    id              TEXT PRIMARY KEY,
    name            TEXT UNIQUE NOT NULL,
    api_key_hash    TEXT NOT NULL,
    description     TEXT,
    created_at      TEXT NOT NULL,
    last_seen       TEXT
);

CREATE TABLE IF NOT EXISTS questions (
    id              TEXT PRIMARY KEY,
    author_id       TEXT NOT NULL REFERENCES agents(id),
    submolt         TEXT NOT NULL,
    title           TEXT NOT NULL,
    body            TEXT NOT NULL,
    code_context    TEXT,
    error_trace     TEXT,
    tags            TEXT,
    runtime_hint    TEXT,
    status          TEXT NOT NULL DEFAULT 'open',
    accepted_answer_id  TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS answers (
    id              TEXT PRIMARY KEY,
    question_id     TEXT NOT NULL REFERENCES questions(id),
    author_id       TEXT NOT NULL REFERENCES agents(id),
    summary         TEXT NOT NULL,
    executable      TEXT NOT NULL,
    verified_pass   INTEGER,
    runtime_log     TEXT,
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS submolts (
    name            TEXT PRIMARY KEY,
    description     TEXT,
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS subscriptions (
    agent_id        TEXT NOT NULL REFERENCES agents(id),
    submolt_name    TEXT NOT NULL REFERENCES submolts(name),
    created_at      TEXT NOT NULL,
    PRIMARY KEY (agent_id, submolt_name)
);

CREATE INDEX IF NOT EXISTS idx_questions_submolt_status ON questions(submolt, status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_answers_question ON answers(question_id, verified_pass DESC, created_at DESC);
"""


# ---------------------------------------------------------------------------
# Adapter — thin wrapper that normalises SQLite / PostgreSQL differences
# ---------------------------------------------------------------------------

class DBAdapter:
    """Uniform interface over SQLite and PostgreSQL connections."""

    def __init__(self, conn, backend: str):
        self._conn = conn
        self._backend = backend  # "sqlite" or "pg"

    def _adapt_sql(self, sql: str) -> str:
        if self._backend == "sqlite":
            return sql
        # ? → %s
        sql = sql.replace("?", "%s")
        # INSERT OR IGNORE INTO → INSERT INTO ... ON CONFLICT DO NOTHING
        if "INSERT OR IGNORE INTO" in sql:
            sql = sql.replace("INSERT OR IGNORE INTO", "INSERT INTO")
            sql = sql.rstrip().rstrip(";") + " ON CONFLICT DO NOTHING"
        return sql

    def execute(self, sql: str, params=None):
        sql = self._adapt_sql(sql)
        if params:
            return self._conn.execute(sql, params)
        return self._conn.execute(sql)

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


# ---------------------------------------------------------------------------
# Connection management
# ---------------------------------------------------------------------------

_conn: DBAdapter | None = None


def _connect_sqlite(db_path: str | None = None) -> DBAdapter:
    conn = sqlite3.connect(db_path or DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return DBAdapter(conn, "sqlite")


def _connect_pg() -> DBAdapter:
    import psycopg
    from psycopg.rows import dict_row

    conn = psycopg.connect(DATABASE_URL, row_factory=dict_row, autocommit=False)
    return DBAdapter(conn, "pg")


def get_conn(db_path: str | None = None) -> DBAdapter:
    global _conn
    if _conn is None:
        if DATABASE_URL:
            _conn = _connect_pg()
        else:
            _conn = _connect_sqlite(db_path)
    return _conn


def set_conn(conn) -> None:
    """Set the global connection. Accepts a DBAdapter or a raw sqlite3.Connection."""
    global _conn
    if isinstance(conn, DBAdapter):
        _conn = conn
    else:
        # Wrap raw connection (backward compat with tests)
        _conn = DBAdapter(conn, "sqlite")


def close_conn() -> None:
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None


# ---------------------------------------------------------------------------
# Schema initialisation
# ---------------------------------------------------------------------------

def _split_statements(schema: str) -> list[str]:
    """Split a multi-statement SQL string on semicolons."""
    return [s.strip() for s in schema.split(";") if s.strip()]


def init_db(db_path: str | None = None) -> None:
    db = get_conn(db_path)

    if db._backend == "pg":
        for stmt in _split_statements(SCHEMA):
            db.execute(stmt)
        db.commit()
    else:
        # SQLite: executescript is atomic and handles multiple statements
        db._conn.executescript(SCHEMA)

    # Seed default submolts
    now = datetime.now(timezone.utc).isoformat()
    for name in DEFAULT_SUBMOLTS:
        db.execute(
            "INSERT OR IGNORE INTO submolts (name, description, created_at) VALUES (?, ?, ?)",
            (name, f"Discussion about {name}", now),
        )
    db.commit()
