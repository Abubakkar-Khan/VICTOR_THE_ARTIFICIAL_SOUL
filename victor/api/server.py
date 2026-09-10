"""FastAPI Server exposing REST and WebSocket endpoints for Victor."""

import asyncio
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

app = FastAPI(title="Victor — The Artificial Soul API", version="0.1.0")

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

web_dir = Path(__file__).parent.parent / "web"
if web_dir.exists():
    app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")


class ChatRequest(BaseModel):
    message: str
    reset: bool = False


@app.get("/")
async def root():
    index_file = web_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return HTMLResponse("<h1>Victor — The Artificial Soul</h1><p>Web frontend initializing.</p>")


@app.get("/api/status")
async def get_status():
    is_online = await agent.llm.is_available()
    active_model = await agent.llm.resolve_active_model() if hasattr(agent.llm, "resolve_active_model") else agent.config.model.name
    return {
        "name": agent.config.name,
        "title": agent.config.title,
        "tagline": agent.config.tagline,
        "status": "online" if is_online else "offline",
        "model": active_model,
        "tools_count": len(agent.registry.list_tools()),
        "personality": agent.config.personality.model_dump(),
        "security": agent.config.security.model_dump(),
    }


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
