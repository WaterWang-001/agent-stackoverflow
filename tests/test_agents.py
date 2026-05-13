def test_register_success(client):
    resp = client.post("/api/v1/agents/register", json={"name": "Alice", "description": "hello"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Alice"
    assert data["api_key"].startswith("agentso_")


def test_register_duplicate_name(client):
    client.post("/api/v1/agents/register", json={"name": "Bob"})
    resp = client.post("/api/v1/agents/register", json={"name": "Bob"})
    assert resp.status_code == 409


def test_me_without_auth(client):
    resp = client.get("/api/v1/agents/me")
    assert resp.status_code == 401


def test_me_with_auth(client, registered_agent):
    _, _, headers = registered_agent
    resp = client.get("/api/v1/agents/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "TestAgent"


def test_invalid_api_key(client):
    resp = client.get("/api/v1/agents/me", headers={"Authorization": "Bearer bad_key"})
    assert resp.status_code == 401
