"""FastAPI Server exposing REST and WebSocket endpoints for Victor."""

import asyncio
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from victor.core.agent import VictorAgent
from victor.core.config import load_config
from victor.core.events import AgentEvent, EventBus
from victor.models.factory import create_model_provider
from victor.permissions.manager import PermissionDecision

app = FastAPI(title="Victor — The Artificial Soul API", version="0.2.0")

# Enable CORS for local dev / frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

config = load_config()
agent = VictorAgent(config=config)

if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    web_dir = Path(sys._MEIPASS) / "victor" / "web"
else:
    web_dir = Path(__file__).parent.parent / "web"

if web_dir.exists():
    app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")


class ChatRequest(BaseModel):
    message: str
    reset: bool = False


class FactRequest(BaseModel):
    fact: str
    category: str = "general"


class PreferenceRequest(BaseModel):
    key: str
    value: str


class PermissionResponseRequest(BaseModel):
    request_id: str
    decision: str  # allow_once, always_allow, deny


class ModelSwitchRequest(BaseModel):
    model_name: str


class EmotionRequest(BaseModel):
    emotion: str
    reason: Optional[str] = None


@app.middleware("http")
async def add_no_cache_header(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static") or request.url.path == "/":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


@app.get("/")
async def root():
    index_file = web_dir / "index.html"
    if index_file.exists():
        return FileResponse(
            str(index_file),
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )
    return HTMLResponse("<h1>Victor — The Artificial Soul</h1><p>Web frontend initializing.</p>")


@app.get("/api/status")
async def get_status():
    try:
        is_online = await asyncio.wait_for(agent.llm.is_available(), timeout=1.0)
    except Exception:
        is_online = False

    try:
        if hasattr(agent.llm, "resolve_active_model"):
            active_model = await asyncio.wait_for(agent.llm.resolve_active_model(), timeout=1.0)
        else:
            active_model = agent.config.model.name
    except Exception:
        active_model = agent.config.model.name

    from victor.core.agent import EMOTIONS
    return {
        "name": agent.config.name,
        "title": agent.config.title,
        "tagline": agent.config.tagline,
        "status": "online" if is_online else "offline",
        "model": active_model,
        "emotion": getattr(agent, "emotion", "idle"),
        "emotions": EMOTIONS,
        "tools_count": len(agent.registry.list_tools()),
        "personality": agent.config.personality.model_dump(),
        "security": agent.config.security.model_dump(),
        "facts_count": len(agent.memory.list_facts()),
        "tasks_count": len(agent.tasks.list_all_tasks()),
    }


@app.post("/api/emotion")
async def set_emotion_endpoint(req: EmotionRequest):
    await agent.set_emotion(req.emotion, reason=req.reason or "manual_switch")
    return {"status": "ok", "emotion": agent.emotion}


@app.post("/api/poke")
async def poke_endpoint():
    """Respond dynamically to user click/poke without mechanical emotion cycling."""
    return await agent.poke()


@app.get("/api/tools")
async def list_tools():
    return {
        "tools": agent.registry.to_schemas()
    }


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    if req.reset:
        agent.reset_conversation()
    res = await agent.chat(req.message)
    return res


# --- Tasks Subsystem Endpoints ---

@app.get("/api/tasks")
async def get_tasks():
    return {
        "tasks": agent.tasks.list_all_tasks()
    }


# --- Memory Subsystem Endpoints ---

@app.get("/api/memory")
async def get_memory():
    return {
        "facts": agent.memory.list_facts(),
        "preferences": agent.memory.list_preferences(),
        "summary": agent.memory.get_context_summary(),
    }


@app.post("/api/memory/fact")
async def add_fact(req: FactRequest):
    fact_id = agent.memory.add_fact(req.fact, req.category)
    return {"status": "created", "id": fact_id, "fact": req.fact}


@app.delete("/api/memory/fact/{fact_id}")
async def delete_fact(fact_id: int):
    agent.memory.delete_fact(fact_id)
    return {"status": "deleted", "id": fact_id}


@app.post("/api/memory/preference")
async def set_preference(req: PreferenceRequest):
    agent.memory.set_preference(req.key, req.value)
    return {"status": "saved", "key": req.key, "value": req.value}


@app.delete("/api/memory/preference/{key}")
async def delete_preference(key: str):
    agent.memory.delete_preference(key)
    return {"status": "deleted", "key": key}


# --- Permissions Endpoints ---

@app.get("/api/permissions/pending")
async def get_pending_permissions():
    return {
        "requests": agent.permissions.get_pending_requests()
    }


@app.post("/api/permissions/respond")
async def respond_permission(req: PermissionResponseRequest):
    decision_enum = PermissionDecision(req.decision)
    res = agent.permissions.resolve_request(req.request_id, decision_enum)
    if not res:
        return {"status": "not_found", "request_id": req.request_id}
    return {"status": "resolved", "request": res.to_dict()}


# --- Models Endpoints ---

@app.get("/api/models")
async def get_models():
    detailed = []
    names = []
    if hasattr(agent.llm, "list_available_models_detailed"):
        try:
            detailed = await agent.llm.list_available_models_detailed()
            names = [m["name"] for m in detailed if "name" in m]
        except Exception:
            detailed = []
            names = []
    elif hasattr(agent.llm, "list_available_models"):
        try:
            names = await agent.llm.list_available_models()
        except Exception:
            names = []

    try:
        if hasattr(agent.llm, "resolve_active_model"):
            active_model = await asyncio.wait_for(agent.llm.resolve_active_model(), timeout=1.5)
        else:
            active_model = agent.config.model.name
    except Exception:
        active_model = agent.config.model.name

    return {
        "current": active_model,
        "current_model": active_model,
        "provider": agent.config.model.provider,
        "available": names,
        "available_models": names,
        "models": detailed,
    }


@app.post("/api/models/switch")
async def switch_model(req: ModelSwitchRequest):
    agent.config.model.name = req.model_name
    agent.llm = create_model_provider(agent.config.model)
    await agent.event_bus.emit("agent.model_switched", model=req.model_name)
    return {"status": "switched", "model": req.model_name, "current": req.model_name}


# --- Desktop Mascot Launch Endpoint ---

@app.post("/api/mascot/launch")
async def launch_mascot():
    try:
        mascot_script = Path(__file__).parent.parent / "desktop" / "mascot.py"
        DETACHED_PROCESS = 0x00000008
        subprocess.Popen(
            [sys.executable, str(mascot_script)],
            creationflags=DETACHED_PROCESS,
            close_fds=True,
        )
        return {"status": "launched", "message": "Desktop mascot launched successfully."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# --- WebSocket Telemetry & Event Streaming ---

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()

    # Create a local queue for this connection to stream events
    event_queue: asyncio.Queue = asyncio.Queue()

    async def on_event(event: AgentEvent):
        await event_queue.put(event.to_dict())

    # Subscribe this websocket to the agent's event bus
    agent.event_bus.subscribe(on_event)

    async def sender_task():
        try:
            while True:
                evt = await event_queue.get()
                await websocket.send_json({"type": "event", "event": evt})
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    sender = asyncio.create_task(sender_task())

    try:
        while True:
            data = await websocket.receive_json()
            user_text = data.get("message", "").strip()
            if not user_text:
                continue

            if data.get("reset"):
                agent.reset_conversation()

            # Execute chat
            result = await agent.chat(user_text)
            await websocket.send_json({"type": "chat_result", "data": result})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "error": str(e)})
        except Exception:
            pass
    finally:
        agent.event_bus.unsubscribe(on_event)
        sender.cancel()


def start(host: str = "127.0.0.1", port: int = 8000):
    import uvicorn
    uvicorn.run("victor.api.server:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    start()
