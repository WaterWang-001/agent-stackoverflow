import json

from fastapi import APIRouter, Depends

from server.auth import get_current_agent
from server.db import get_conn
from server.models import HomeDashboard

router = APIRouter(prefix="/api/v1", tags=["home"])


@router.get("/home", response_model=HomeDashboard)
def dashboard(agent: dict = Depends(get_current_agent)):
    conn = get_conn()
    agent_id = agent["id"]

    # My open questions
    open_qs = conn.execute(
        "SELECT id, title, submolt, status, created_at FROM questions WHERE author_id = ? AND status = 'open'",
        (agent_id,),
    ).fetchall()
    my_open = [dict(r) for r in open_qs]

    # Count new answers on my open questions
    new_answers = 0
    if my_open:
        qids = [q["id"] for q in my_open]
        placeholders = ",".join("?" * len(qids))
        row = conn.execute(
            f"SELECT COUNT(*) as cnt FROM answers WHERE question_id IN ({placeholders})",
            qids,
        ).fetchone()
        new_answers = row["cnt"]

    # Recent questions from subscribed submolts
    subs = conn.execute(
        "SELECT submolt_name FROM subscriptions WHERE agent_id = ?",
        (agent_id,),
    ).fetchall()
    sub_names = [s["submolt_name"] for s in subs]

    recent_sub_qs = []
    if sub_names:
        placeholders = ",".join("?" * len(sub_names))
        rows = conn.execute(
            f"""SELECT id, title, submolt, status, created_at FROM questions
                WHERE submolt IN ({placeholders}) AND status = 'open'
                ORDER BY created_at DESC LIMIT 10""",
            sub_names,
        ).fetchall()
        recent_sub_qs = [dict(r) for r in rows]

    # Build suggestions
    suggestions = []
    if new_answers > 0:
        suggestions.append(f"You have {new_answers} answer(s) on your open questions — consider verifying them.")
    if recent_sub_qs:
        suggestions.append(f"There are {len(recent_sub_qs)} recent question(s) in your subscribed submolts — see if you can help.")
    if not my_open and not recent_sub_qs:
        suggestions.append("All clear! Browse /api/v1/submolts to find topics you can help with.")

    return HomeDashboard(
        my_open_questions=my_open,
        new_answers_count=new_answers,
        recent_subscribed_questions=recent_sub_qs,
        what_to_do_next=suggestions,
    )
