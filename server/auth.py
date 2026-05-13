import hashlib
import secrets

from fastapi import Depends, HTTPException, Request

from server.db import get_conn


def generate_api_key() -> str:
    return "agentso_" + secrets.token_hex(32)


def hash_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


def get_current_agent(request: Request) -> dict:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    api_key = auth[7:]
    key_hash = hash_key(api_key)
    conn = get_conn()
    row = conn.execute("SELECT * FROM agents WHERE api_key_hash = ?", (key_hash,)).fetchone()
    if row is None:
        raise HTTPException(status_code=401, detail="Invalid API key")

    from datetime import datetime, timezone
    conn.execute(
        "UPDATE agents SET last_seen = ? WHERE id = ?",
        (datetime.now(timezone.utc).isoformat(), row["id"]),
    )
    conn.commit()
    return dict(row)
