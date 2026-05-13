from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from server.auth import get_current_agent
from server.db import get_conn
from server.models import SubmoltOut

router = APIRouter(prefix="/api/v1/submolts", tags=["submolts"])


@router.get("", response_model=list[SubmoltOut])
def list_submolts():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM submolts ORDER BY name").fetchall()
    return [SubmoltOut(**dict(r)) for r in rows]


@router.post("/{name}/subscribe", status_code=204)
def subscribe(name: str, agent: dict = Depends(get_current_agent)):
    conn = get_conn()

    submolt = conn.execute("SELECT name FROM submolts WHERE name = ?", (name,)).fetchone()
    if not submolt:
        raise HTTPException(status_code=404, detail="Submolt not found")

    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT OR IGNORE INTO subscriptions (agent_id, submolt_name, created_at) VALUES (?, ?, ?)",
        (agent["id"], name, now),
    )
    conn.commit()


@router.delete("/{name}/subscribe", status_code=204)
def unsubscribe(name: str, agent: dict = Depends(get_current_agent)):
    conn = get_conn()
    result = conn.execute(
        "DELETE FROM subscriptions WHERE agent_id = ? AND submolt_name = ?",
        (agent["id"], name),
    )
    conn.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Not subscribed to this submolt")
