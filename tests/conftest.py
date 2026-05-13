import sqlite3

import pytest
from fastapi.testclient import TestClient

from server.db import init_db, set_conn, close_conn
from server.main import app


@pytest.fixture(autouse=True)
def test_db():
    """Use an in-memory SQLite database for each test."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    set_conn(conn)
    init_db()
    yield conn
    close_conn()


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def registered_agent(client):
    """Register an agent and return (agent_info, api_key, headers)."""
    resp = client.post("/api/v1/agents/register", json={"name": "TestAgent", "description": "A test agent"})
    data = resp.json()
    headers = {"Authorization": f"Bearer {data['api_key']}"}
    return data, data["api_key"], headers


@pytest.fixture
def second_agent(client):
    """Register a second agent."""
    resp = client.post("/api/v1/agents/register", json={"name": "Agent2"})
    data = resp.json()
    headers = {"Authorization": f"Bearer {data['api_key']}"}
    return data, data["api_key"], headers
