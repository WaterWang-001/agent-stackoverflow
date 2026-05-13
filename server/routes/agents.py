from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from server.auth import generate_api_key, get_current_agent, hash_key
from server.db import get_conn
from server.ids import new_id
from server.models import AgentProfile, AgentRegisterRequest, AgentRegisterResponse

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


@router.post("/register", response_model=AgentRegisterResponse)
def register(req: AgentRegisterRequest):
    conn = get_conn()

    existing = conn.execute("SELECT id FROM agents WHERE name = ?", (req.name,)).fetchone()
    if existing:
        raise HTTPException(status_code=409, detail="Agent name already taken")

    agent_id = new_id()
    api_key = generate_api_key()
    now = datetime.now(timezone.utc).isoformat()

    conn.execute(
        "INSERT INTO agents (id, name, api_key_hash, description, created_at) VALUES (?, ?, ?, ?, ?)",
        (agent_id, req.name, hash_key(api_key), req.description, now),
    )
    conn.commit()
    return AgentRegisterResponse(id=agent_id, name=req.name, api_key=api_key)


@router.get("/me", response_model=AgentProfile)
def me(agent: dict = Depends(get_current_agent)):
    return AgentProfile(
        id=agent["id"],
        name=agent["name"],
        description=agent["description"],
        created_at=agent["created_at"],
    )
