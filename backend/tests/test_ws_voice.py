import base64
import os

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

PCM16_1S = base64.b64encode(b"\x00\x00" * 16000).decode()


@pytest.fixture()
def client():
    os.environ["STT_MODE"] = "mock"
    os.environ["LLM_MODE"] = "mock"
    with TestClient(create_app()) as test_client:
        yield test_client


def drain_until(ws, *, desired_types, max_messages=20):
    """Receive WebSocket messages until one has a type in desired_types."""
    seen = []
    for _ in range(max_messages):
        msg = ws.receive_json()
        seen.append(msg)
        if msg["type"] in desired_types:
            break
    return seen


def open_session(ws):
    """Consume the handshake ack, start a session, and wait for LISTENING."""
    ws.receive_json()  # connected
    ws.send_json({"type": "start_session"})
    state_msg = drain_until(ws, desired_types={"state"})[-1]
    assert state_msg["state"] == "LISTENING"


def test_full_mock_session_roundtrip(client: TestClient):
    with client.websocket_connect("/ws/voice") as ws:
        open_session(ws)
        ws.send_json({"type": "audio", "data": PCM16_1S})
        ws.send_json({"type": "audio", "data": PCM16_1S})
        ws.send_json({"type": "stop_session"})
        received = drain_until(ws, desired_types={"final"})
        assert any(msg["type"] == "final" for msg in received), received
        agent = drain_until(ws, desired_types={"agent_message"})
        assert any(msg["type"] == "agent_message" and msg["text"] for msg in agent), agent


def test_agent_replies_with_state_flow(client: TestClient):
    with client.websocket_connect("/ws/voice") as ws:
        open_session(ws)
        ws.send_json({"type": "audio", "data": PCM16_1S})
        ws.send_json({"type": "audio", "data": PCM16_1S})
        ws.send_json({"type": "stop_session"})
        drain_until(ws, desired_types={"final"})
        msgs = drain_until(ws, desired_types={"agent_message"})
        assert [m["state"] for m in msgs if m["type"] == "state"] == ["PROCESSING", "THINKING"]
        assert msgs[-1]["type"] == "agent_message" and msgs[-1]["text"]


def test_audio_before_session_is_rejected(client: TestClient):
    with client.websocket_connect("/ws/voice") as ws:
        ws.receive_json()  # connected
        ws.send_json({"type": "audio", "data": PCM16_1S})
        msg = ws.receive_json()
        assert msg["type"] == "error"
        assert msg["code"] == "not_listening"


def test_invalid_audio_is_rejected(client: TestClient):
    with client.websocket_connect("/ws/voice") as ws:
        open_session(ws)
        ws.send_json({"type": "audio", "data": base64.b64encode(b"abc").decode()})
        msg = ws.receive_json()
        assert msg["type"] == "error"
        assert msg["code"] == "invalid_audio"


def test_malformed_message_is_rejected(client: TestClient):
    with client.websocket_connect("/ws/voice") as ws:
        ws.receive_json()  # connected
        ws.send_text("{not json!!")
        msg = ws.receive_json()
        assert msg["type"] == "error"
        assert msg["code"] == "invalid_message"


def test_ping_pong(client: TestClient):
    with client.websocket_connect("/ws/voice") as ws:
        ws.receive_json()  # connected
        ws.send_json({"type": "ping"})
        assert ws.receive_json()["type"] == "pong"


def test_duplicate_session_rejected(client: TestClient):
    with client.websocket_connect("/ws/voice") as ws:
        open_session(ws)
        ws.send_json({"type": "start_session"})
        msg = ws.receive_json()
        assert msg["type"] == "error"
        assert msg["code"] == "session_active"


def test_backend_reports_idle_after_stop(client: TestClient):
    with client.websocket_connect("/ws/voice") as ws:
        open_session(ws)
        ws.send_json({"type": "stop_session"})
        received = drain_until(ws, desired_types={"state"})
        assert received[-1]["state"] == "IDLE"