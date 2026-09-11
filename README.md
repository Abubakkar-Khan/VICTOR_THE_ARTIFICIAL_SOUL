# Victor — The Artificial Soul

A little creature for your computer.

Victor is a local desktop AI companion. It lives quietly on your desktop as a small animated character. When you need it, it can chat, search the web, find videos, read files, open applications, and control your computer.

---

## What it does

- **Chat** naturally in a calm, typography-first interface
- **Search the web** by just asking
- **Find YouTube videos** by describing what you want
- **Read local files** from your workspace
- **Open applications** like Chrome, VS Code, Spotify
- **Control the computer** with mouse clicks and screen inspection
- **Send notifications** through system toasts
- **Run shell commands** (with permission)
- **Remember things** you tell it across sessions

Victor uses a local language model (Ollama) and works entirely offline. No data leaves your machine.

---

## Getting started

### Requirements

- Python 3.10+
- [Ollama](https://ollama.ai/) with a small model installed

### Install

```bash
git clone https://github.com/your-username/Victor_The_Artificial_Soul.git
cd Victor_The_Artificial_Soul
pip install -r requirements.txt
ollama pull qwen2:1.5b
```

### Run

```bash
python -m victor.api.server
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

To launch the desktop companion:
```bash
python -m victor.desktop.mascot
```

Or click "Launch" in Settings within the workshop.

### CLI

```bash
python -m victor.cli
```

---

## Architecture

Victor has two layers:

**Python backend** — FastAPI server with WebSocket support, running the agent loop, tools, memory, and model inference.

**Web frontend** — A quiet, typography-first single-page application served as static files.

```
victor/
  core/
    agent.py       — Agent orchestrator
    personality.py — System prompt builder
    events.py      — Async event bus
    config.py      — YAML config loader
  models/
    base.py        — LLM abstraction
    ollama.py      — Local Ollama provider
    remote.py      — OpenAI-compatible provider
    factory.py     — Provider factory
  tools/
    base.py        — Tool contract (BaseTool, ToolResult)
    router.py      — Intent-based tool router
    registry.py    — Tool registry
    factory.py     — Tool factory
    calculator.py  — Math evaluation (AST-based, no eval)
    web_search.py  — DuckDuckGo search
    browser.py     — Webpage text extraction
    youtube.py     — YouTube video search
    filesystem.py  — Local file reader
    applications.py — App launcher
    computer.py    — Mouse/screen control (Win32 ctypes)
    notifications.py — System notifications
    shell.py       — Shell command execution
  memory/
    store.py       — SQLite persistence
  tasks/
    manager.py     — Multi-step task tracking
  permissions/
    manager.py     — Permission levels and approval
  desktop/
    mascot.py      — Pixel-art desktop companion (tkinter)
  api/
    server.py      — FastAPI REST + WebSocket server
  web/
    index.html     — Workshop interface
    style.css      — Design system
    app.js         — Client logic
  cli.py           — Terminal interface
config/
  victor.yaml      — Configuration
tests/             — Test suite
```

---

## Tools

| Tool | What it does | Permission |
|------|-------------|------------|
| calculator | Evaluates math expressions safely | Safe |
| web_search | Searches the web via DuckDuckGo | Safe |
| browser | Extracts text from webpages | Controlled |
| youtube | Searches YouTube for videos | Safe |
| filesystem | Reads local files | Controlled |
| applications | Opens desktop applications | Safe |
| computer | Controls mouse and inspects screen | Controlled |
| notifications | Sends system notifications | Safe |
| shell | Runs shell commands | Dangerous |

Victor auto-detects which tool to use from natural language. You can also use slash commands like `/calc`, `/search`, `/browse`.

---

## Design

The interface follows a simple principle: warm, quiet, typography-first.

- Dark warm surfaces, not black
- One accent color (warm amber), not a rainbow
- Text-driven, not card-driven
- Tool activity shown as small inline annotations, not dashboards
- Memory looks like a notebook, not a database
- The overall feeling: someone cared about this software

---

## Configuration

Edit `config/victor.yaml`:

```yaml
name: "Victor"
title: "The Artificial Soul"
tagline: "A little creature for your computer."

personality:
  curiosity: "high"
  humor: "low"
  formality: "medium"
  enthusiasm: "low"
  tone: "Quiet, warm, thoughtful companion."

model:
  provider: "ollama"
  name: "qwen2:1.5b"
  fallback_model: "qwen3.5:2b"
  temperature: 0.5
  max_tokens: 512

security:
  allow_shell: false
  allowed_file_roots:
    - "."
```

---

## Tests

```bash
python -m pytest -v tests/
```

---

## License

MIT
