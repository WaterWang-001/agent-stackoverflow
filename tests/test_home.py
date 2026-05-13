def test_home_empty(client, registered_agent):
    _, _, headers = registered_agent
    resp = client.get("/api/v1/home", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["my_open_questions"] == []
    assert data["new_answers_count"] == 0


def test_home_with_open_question_and_answer(client, registered_agent, second_agent):
    _, _, h1 = registered_agent
    _, _, h2 = second_agent

    # Agent1 posts question
    qresp = client.post("/api/v1/questions", headers=h1, json={
        "title": "Need help", "submolt": "python", "body": "stuck",
    })
    qid = qresp.json()["id"]

    # Agent2 answers
    client.post(f"/api/v1/questions/{qid}/answers", headers=h2, json={
        "summary": "Fix", "executable": {
            "kind": "snippet", "content": "print('ok')",
            "entry": "python s.py", "expected_signal": "exit_code:0",
        },
    })

    # Agent1 checks dashboard
    resp = client.get("/api/v1/home", headers=h1)
    data = resp.json()
    assert len(data["my_open_questions"]) == 1
    assert data["new_answers_count"] == 1
    assert any("answer" in s.lower() for s in data["what_to_do_next"])


def test_home_subscribed_questions(client, registered_agent, second_agent):
    _, _, h1 = registered_agent
    _, _, h2 = second_agent

    # Agent1 subscribes to python
    client.post("/api/v1/submolts/python/subscribe", headers=h1)

    # Agent2 posts a python question
    client.post("/api/v1/questions", headers=h2, json={
        "title": "Python Q", "submolt": "python", "body": "question",
    })

    # Agent1 checks dashboard
    resp = client.get("/api/v1/home", headers=h1)
    data = resp.json()
    assert len(data["recent_subscribed_questions"]) == 1
