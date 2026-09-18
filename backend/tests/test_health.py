import os

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture()
def client():
    os.environ["STT_MODE"] = "mock"
    os.environ["LLM_MODE"] = "mock"
    with TestClient(create_app()) as test_client:
        yield test_client


def test_health_ok(client: TestClient):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "dataforge-voice-backend"
    assert body["stt_mode"] == "mock"
    assert body["llm_mode"] == "mock"
    assert body["agent_enabled"] is True


def test_root_info(client: TestClient):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["service"] == "DataForge Voice Agent API"