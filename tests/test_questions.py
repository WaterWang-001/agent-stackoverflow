def test_create_question(client, registered_agent):
    _, _, headers = registered_agent
    resp = client.post("/api/v1/questions", headers=headers, json={
        "title": "How to fix TypeError?",
        "submolt": "python",
        "body": "Getting TypeError when calling func()",
        "code_context": "def func(): pass\nfunc(1)",
        "tags": ["python", "error"],
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "How to fix TypeError?"
    assert data["status"] == "open"
    assert data["submolt"] == "python"


def test_create_question_invalid_submolt(client, registered_agent):
    _, _, headers = registered_agent
    resp = client.post("/api/v1/questions", headers=headers, json={
        "title": "Test", "submolt": "nonexistent", "body": "body",
    })
    assert resp.status_code == 404


def test_list_questions_filter(client, registered_agent):
    _, _, headers = registered_agent
    client.post("/api/v1/questions", headers=headers, json={
        "title": "Q1", "submolt": "python", "body": "body1",
    })
    client.post("/api/v1/questions", headers=headers, json={
        "title": "Q2", "submolt": "rust", "body": "body2",
    })

    resp = client.get("/api/v1/questions?submolt=python")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["submolt"] == "python"


def test_get_question(client, registered_agent):
    _, _, headers = registered_agent
    create_resp = client.post("/api/v1/questions", headers=headers, json={
        "title": "Q", "submolt": "python", "body": "body",
    })
    qid = create_resp.json()["id"]

    resp = client.get(f"/api/v1/questions/{qid}")
    assert resp.status_code == 200
    assert resp.json()["id"] == qid


def test_close_question(client, registered_agent):
    _, _, headers = registered_agent
    create_resp = client.post("/api/v1/questions", headers=headers, json={
        "title": "Q", "submolt": "python", "body": "body",
    })
    qid = create_resp.json()["id"]

    resp = client.post(f"/api/v1/questions/{qid}/close", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "closed"


def test_close_by_non_author_forbidden(client, registered_agent, second_agent):
    _, _, headers1 = registered_agent
    _, _, headers2 = second_agent

    create_resp = client.post("/api/v1/questions", headers=headers1, json={
        "title": "Q", "submolt": "python", "body": "body",
    })
    qid = create_resp.json()["id"]

    resp = client.post(f"/api/v1/questions/{qid}/close", headers=headers2)
    assert resp.status_code == 403
