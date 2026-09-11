"""Integration tests for Victor FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from victor.api.server import app

client = TestClient(app)


def test_root_endpoint():
    res = client.get("/")
    assert res.status_code == 200
    assert "Victor" in res.text


def test_api_status():
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Victor"
    assert data["tools_count"] >= 5
    assert "personality" in data


def test_api_tools():
    res = client.get("/api/tools")
    assert res.status_code == 200
    data = res.json()
    assert "tools" in data
    tool_names = [t["name"] for t in data["tools"]]
    assert "calculator" in tool_names
    assert "web_search" in tool_names
    assert "filesystem" in tool_names


def test_api_chat_slash_calc():
    res = client.post("/api/chat", json={"message": "/calc 12 * 12"})
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "tool_result"
    assert data["tool_executed"] == "calculator"
    assert "144" in data["content"]


def test_api_emotion_switch():
    res = client.post("/api/emotion", json={"emotion": "excited", "reason": "user_click"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["emotion"] == "excited"

    status_res = client.get("/api/status")
    assert status_res.status_code == 200
    assert status_res.json()["emotion"] == "excited"


def test_api_models_listing_and_switch():
    res = client.get("/api/models")
    assert res.status_code == 200
    data = res.json()
    assert "current" in data
    assert "available" in data
    assert "available_models" in data
    assert isinstance(data["available"], list)

    switch_res = client.post("/api/models/switch", json={"model_name": "qwen:0.5b"})
    assert switch_res.status_code == 200
    switch_data = switch_res.json()
    assert switch_data["status"] == "switched"
    assert switch_data["model"] == "qwen:0.5b"


def test_api_poke():
    # Set to idle, poke should wake Victor up to neutral
    client.post("/api/emotion", json={"emotion": "idle"})
    poke_res = client.post("/api/poke")
    assert poke_res.status_code == 200
    poke_data = poke_res.json()
    assert poke_data["status"] == "ok"
    assert poke_data["emotion"] == "neutral"
    assert "Awake" in poke_data["message"]


def test_api_mascot_visibility_and_status():
    res = client.post("/api/mascot/visibility", json={"active": True})
    assert res.status_code == 200
    assert res.json()["workshop_focused"] is True

    status_res = client.get("/api/mascot/status")
    assert status_res.status_code == 200
    data = status_res.json()
    assert data["workshop_focused"] is True
    assert "companion_options" in data

    # Unfocus
    res2 = client.post("/api/mascot/visibility", json={"active": False})
    assert res2.status_code == 200
    assert res2.json()["workshop_focused"] is False


def test_api_mascot_options():
    res = client.post("/api/mascot/options", json={"auto_hide": False, "scale": "compact"})
    assert res.status_code == 200
    opts = res.json()["companion_options"]
    assert opts["auto_hide"] is False
    assert opts["scale"] == "compact"


def test_api_stt_text_passthrough():
    res = client.post("/api/stt", json={"text": "hello victor"})
    assert res.status_code == 200
    assert res.json()["text"] == "hello victor"


