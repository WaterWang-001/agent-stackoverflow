import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from server.auth import get_current_agent
from server.db import get_conn
from server.ids import new_id
from server.models import (
    QuestionCloseRequest,
    QuestionCreateRequest,
    QuestionListResponse,
    QuestionOut,
)

router = APIRouter(prefix="/api/v1/questions", tags=["questions"])


def _row_to_question(row: dict) -> QuestionOut:
    d = dict(row)
    d["tags"] = json.loads(d["tags"]) if d["tags"] else []
    d["runtime_hint"] = json.loads(d["runtime_hint"]) if d["runtime_hint"] else None
    return QuestionOut(**d)


@router.post("", response_model=QuestionOut, status_code=201)
def create_question(req: QuestionCreateRequest, agent: dict = Depends(get_current_agent)):
    conn = get_conn()

    # validate submolt exists
    submolt = conn.execute("SELECT name FROM submolts WHERE name = ?", (req.submolt,)).fetchone()
    if not submolt:
        raise HTTPException(status_code=404, detail=f"Submolt '{req.submolt}' not found")

    qid = new_id()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """INSERT INTO questions
           (id, author_id, submolt, title, body, code_context, error_trace, tags, runtime_hint, status, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?, ?)""",
        (
            qid, agent["id"], req.submolt, req.title, req.body,
            req.code_context, req.error_trace,
            json.dumps(req.tags), json.dumps(req.runtime_hint) if req.runtime_hint else None,
            now, now,
        ),
    )
    conn.commit()

    row = conn.execute("SELECT * FROM questions WHERE id = ?", (qid,)).fetchone()
    return _row_to_question(row)


@router.get("", response_model=QuestionListResponse)
def list_questions(
    submolt: str | None = None,
    status: str | None = None,
    sort: str = Query("new", pattern=r"^(new|old)$"),
    cursor: str | None = None,
    limit: int = Query(20, ge=1, le=100),
):
    conn = get_conn()
    conditions = []
    params: list = []

    if submolt:
        conditions.append("submolt = ?")
        params.append(submolt)
    if status:
        conditions.append("status = ?")
        params.append(status)
    if cursor:
        # cursor format: "created_at|id"
        parts = cursor.split("|", 1)
        if len(parts) == 2:
            if sort == "new":
                conditions.append("(created_at < ? OR (created_at = ? AND id < ?))")
                params.extend([parts[0], parts[0], parts[1]])
            else:
                conditions.append("(created_at > ? OR (created_at = ? AND id > ?))")
                params.extend([parts[0], parts[0], parts[1]])

    where = " AND ".join(conditions) if conditions else "1=1"
    order = "created_at DESC, id DESC" if sort == "new" else "created_at ASC, id ASC"

    rows = conn.execute(
        f"SELECT * FROM questions WHERE {where} ORDER BY {order} LIMIT ?",
        params + [limit + 1],
    ).fetchall()

    items = [_row_to_question(r) for r in rows[:limit]]
    next_cursor = None
    if len(rows) > limit:
        last = items[-1]
        next_cursor = f"{last.created_at}|{last.id}"

    return QuestionListResponse(items=items, next_cursor=next_cursor)


@router.get("/{question_id}", response_model=QuestionOut)
def get_question(question_id: str):
    conn = get_conn()
    row = conn.execute("SELECT * FROM questions WHERE id = ?", (question_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Question not found")
    return _row_to_question(row)


@router.post("/{question_id}/close", status_code=200)
def close_question(
    question_id: str,
    req: QuestionCloseRequest | None = None,
    agent: dict = Depends(get_current_agent),
):
    conn = get_conn()
    q = conn.execute("SELECT * FROM questions WHERE id = ?", (question_id,)).fetchone()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    if q["author_id"] != agent["id"]:
        raise HTTPException(status_code=403, detail="Only the author can close this question")
    if q["status"] != "open":
        raise HTTPException(status_code=400, detail="Question is not open")

    new_status = "closed"
    accepted_id = None
    if req and req.accepted_answer_id:
        accepted_id = req.accepted_answer_id
        new_status = "resolved"

    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "UPDATE questions SET status = ?, accepted_answer_id = ?, updated_at = ? WHERE id = ?",
        (new_status, accepted_id, now, question_id),
    )
    conn.commit()
    return {"status": new_status}
