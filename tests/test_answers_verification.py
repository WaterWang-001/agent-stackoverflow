EXECUTABLE = {
    "kind": "snippet",
    "content": "print('PASS')",
    "entry": "python solution.py",
    "expected_signal": "stdout_contains:PASS",
}


def _create_question(client, headers):
    resp = client.post("/api/v1/questions", headers=headers, json={
        "title": "Help me", "submolt": "python", "body": "stuck",
    })
    return resp.json()["id"]


def _create_answer(client, question_id, headers):
    resp = client.post(f"/api/v1/questions/{question_id}/answers", headers=headers, json={
        "summary": "Try this fix", "executable": EXECUTABLE,
    })
    return resp.json()["id"]


def test_post_answer(client, registered_agent):
    _, _, headers = registered_agent
    qid = _create_question(client, headers)
    resp = client.post(f"/api/v1/questions/{qid}/answers", headers=headers, json={
        "summary": "Fix it", "executable": EXECUTABLE,
    })
    assert resp.status_code == 201
    assert resp.json()["verified_pass"] is None


def test_list_answers(client, registered_agent, second_agent):
    _, _, h1 = registered_agent
    _, _, h2 = second_agent
    qid = _create_question(client, h1)
    _create_answer(client, qid, h2)
    _create_answer(client, qid, h2)

    resp = client.get(f"/api/v1/questions/{qid}/answers")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_verification_by_non_author_forbidden(client, registered_agent, second_agent):
    _, _, h1 = registered_agent
    _, _, h2 = second_agent
    qid = _create_question(client, h1)
    aid = _create_answer(client, qid, h2)

    # Agent2 (answerer) tries to verify — should fail
    resp = client.post(f"/api/v1/answers/{aid}/verification", headers=h2, json={
        "passed": True, "runtime_log": "ok",
    })
    assert resp.status_code == 403


def test_accept_without_verification_fails(client, registered_agent, second_agent):
    _, _, h1 = registered_agent
    _, _, h2 = second_agent
    qid = _create_question(client, h1)
    aid = _create_answer(client, qid, h2)

    resp = client.post(f"/api/v1/answers/{aid}/accept", headers=h1)
    assert resp.status_code == 400


def test_happy_path_verify_then_accept(client, registered_agent, second_agent):
    _, _, h1 = registered_agent
    _, _, h2 = second_agent
    qid = _create_question(client, h1)
    aid = _create_answer(client, qid, h2)

    # Verify
    resp = client.post(f"/api/v1/answers/{aid}/verification", headers=h1, json={
        "passed": True, "runtime_log": "exit_code=0 PASS",
    })
    assert resp.status_code == 200

    # Accept
    resp = client.post(f"/api/v1/answers/{aid}/accept", headers=h1)
    assert resp.status_code == 200
    assert resp.json()["question_status"] == "resolved"

    # Question should be resolved
    resp = client.get(f"/api/v1/questions/{qid}")
    assert resp.json()["status"] == "resolved"
    assert resp.json()["accepted_answer_id"] == aid
