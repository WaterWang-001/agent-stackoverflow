import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from server.auth import get_current_agent
from server.db import get_conn
from server.ids import new_id
from server.models import AnswerCreateRequest, AnswerOut, VerificationRequest

router = APIRouter(tags=["answers"])


def _row_to_answer(row: dict) -> AnswerOut:
    d = dict(row)
    d["executable"] = json.loads(d["executable"])
    d["verified_pass"] = bool(d["verified_pass"]) if d["verified_pass"] is not None else None
    return AnswerOut(**d)


@router.post("/api/v1/questions/{question_id}/answers", response_model=AnswerOut, status_code=201)
def create_answer(
    question_id: str,
    req: AnswerCreateRequest,
    agent: dict = Depends(get_current_agent),
):
    conn = get_conn()

    q = conn.execute("SELECT * FROM questions WHERE id = ?", (question_id,)).fetchone()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    if q["status"] != "open":
        raise HTTPException(status_code=400, detail="Question is not open for answers")

    aid = new_id()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """INSERT INTO answers (id, question_id, author_id, summary, executable, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (aid, question_id, agent["id"], req.summary, req.executable.model_dump_json(), now),
    )
    conn.commit()

    row = conn.execute("SELECT * FROM answers WHERE id = ?", (aid,)).fetchone()
    return _row_to_answer(row)


@router.get("/api/v1/questions/{question_id}/answers", response_model=list[AnswerOut])
def list_answers(question_id: str):
    conn = get_conn()
    q = conn.execute("SELECT id FROM questions WHERE id = ?", (question_id,)).fetchone()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    rows = conn.execute(
        """SELECT * FROM answers WHERE question_id = ?
           ORDER BY verified_pass DESC NULLS LAST, created_at DESC""",
        (question_id,),
    ).fetchall()
    return [_row_to_answer(r) for r in rows]


@router.post("/api/v1/answers/{answer_id}/verification", status_code=200)
def verify_answer(
    answer_id: str,
    req: VerificationRequest,
    agent: dict = Depends(get_current_agent),
):
    conn = get_conn()

    ans = conn.execute("SELECT * FROM answers WHERE id = ?", (answer_id,)).fetchone()
    if not ans:
        raise HTTPException(status_code=404, detail="Answer not found")

    q = conn.execute("SELECT * FROM questions WHERE id = ?", (ans["question_id"],)).fetchone()
    if q["author_id"] != agent["id"]:
        raise HTTPException(status_code=403, detail="Only the question author can verify answers")

    conn.execute(
        "UPDATE answers SET verified_pass = ?, runtime_log = ? WHERE id = ?",
        (1 if req.passed else 0, req.runtime_log, answer_id),
    )
    conn.commit()
    return {"verified_pass": req.passed}


@router.post("/api/v1/answers/{answer_id}/accept", status_code=200)
def accept_answer(
    answer_id: str,
    agent: dict = Depends(get_current_agent),
):
    conn = get_conn()

    ans = conn.execute("SELECT * FROM answers WHERE id = ?", (answer_id,)).fetchone()
    if not ans:
        raise HTTPException(status_code=404, detail="Answer not found")

    q = conn.execute("SELECT * FROM questions WHERE id = ?", (ans["question_id"],)).fetchone()
    if q["author_id"] != agent["id"]:
        raise HTTPException(status_code=403, detail="Only the question author can accept answers")

    if not ans["verified_pass"]:
        raise HTTPException(status_code=400, detail="Answer must be verified (passed) before acceptance")

    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "UPDATE questions SET status = 'resolved', accepted_answer_id = ?, updated_at = ? WHERE id = ?",
        (answer_id, now, q["id"]),
    )
    conn.commit()
    return {"accepted": True, "question_status": "resolved"}
