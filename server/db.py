import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from server.config import DB_PATH, DEFAULT_SUBMOLTS

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


def _connect(db_path: str | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path or DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


_conn: sqlite3.Connection | None = None


def get_conn(db_path: str | None = None) -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = _connect(db_path)
    return _conn


def set_conn(conn: sqlite3.Connection) -> None:
    global _conn
    _conn = conn


def close_conn() -> None:
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None


def init_db(db_path: str | None = None) -> None:
    conn = get_conn(db_path)
    conn.executescript(SCHEMA)

    now = datetime.now(timezone.utc).isoformat()
    for name in DEFAULT_SUBMOLTS:
        conn.execute(
            "INSERT OR IGNORE INTO submolts (name, description, created_at) VALUES (?, ?, ?)",
            (name, f"Discussion about {name}", now),
        )
    conn.commit()
