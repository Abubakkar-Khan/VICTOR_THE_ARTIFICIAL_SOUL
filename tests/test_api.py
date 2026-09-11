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
