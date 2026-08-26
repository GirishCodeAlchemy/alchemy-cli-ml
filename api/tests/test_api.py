"""Tests for the FastAPI application."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client with initialized engine."""
    from api.app import app, engine as global_engine
    import api.app as api_module
    from alchemy_ml.inference import InferenceEngine

    # Initialize engine for tests
    eng = InferenceEngine()
    eng.load_commands()
    api_module.engine = eng

    with TestClient(app) as c:
        yield c


class TestHealthEndpoint:
    def test_health(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("healthy", "degraded")
        assert "version" in data
        assert "commands" in data


class TestAskEndpoint:
    def test_ask_basic(self, client):
        resp = client.post("/api/v1/ask", json={
            "query": "list kubernetes pods",
            "top_k": 3,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "query" in data
        assert "results" in data

    def test_ask_empty_query(self, client):
        resp = client.post("/api/v1/ask", json={
            "query": "",
        })
        assert resp.status_code == 200


class TestCommandsEndpoint:
    def test_list_commands(self, client):
        resp = client.get("/api/v1/commands?limit=10")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        if data:
            assert "id" in data[0]
            assert "command" in data[0]

    def test_filter_by_technology(self, client):
        resp = client.get("/api/v1/commands?technology=kubernetes&limit=5")
        assert resp.status_code == 200
        data = resp.json()
        for cmd in data:
            assert cmd["technology"] == "kubernetes"

    def test_get_command_not_found(self, client):
        resp = client.get("/api/v1/commands/nonexistent-id")
        assert resp.status_code == 404


class TestCategoriesEndpoint:
    def test_list_categories(self, client):
        resp = client.get("/api/v1/categories")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)


class TestTechnologiesEndpoint:
    def test_list_technologies(self, client):
        resp = client.get("/api/v1/technologies")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)


class TestSearchEndpoint:
    def test_search(self, client):
        resp = client.get("/api/v1/search?q=pods")
        assert resp.status_code == 200
        data = resp.json()
        assert "query" in data
        assert "results" in data
