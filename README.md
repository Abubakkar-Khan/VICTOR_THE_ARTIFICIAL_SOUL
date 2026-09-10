# Victor — The Artificial Soul

> *"A small artificial mind with a world of tools."*

Victor is a local-first, modular AI agent harness designed to feel like a small artificial being living inside the user's computer.

---

## 🗺️ Progressive Version Roadmap

| Version | Milestone | Core Capabilities |
| :--- | :--- | :--- |
| **v0.1** | **The Harness & Brain** *(Current)* | Modular tool harness, safe execution contract, Ollama & Remote model layer, ReAct reasoning & direct slash commands, rich interactive CLI, dark command-center Web UI. |
| **v0.2** | **The Live Nervous System** | Asynchronous event bus with WebSocket pub/sub, real-time visual DAG execution graph (React Flow), live timing and input/output node inspectors. |
| **v0.3** | **The Memory & Recall** | SQLite episodic conversation persistence, user-curated long-term memory, semantic embeddings / vector RAG, `/remember` & `/forget` commands. |
| **v0.4** | **The Voice (Ears & Speech)** | Local Whisper STT (push-to-talk & continuous), local Piper/Kokoro TTS, emotional presentation states (neutral, curious, excited, concerned), audio waveforms. |
| **v0.5** | **Autonomous Mind & Safety** | Autonomous multi-step task decomposition and tool chaining, model hot-swapping, permission prompt modals for sensitive actions. |

---

## ⚡ Features in v0.1

- **Standardized Tool Harness (`victor/tools/`)**:
  - `BaseTool` abstract contract with JSON schema parameter validation, timing, and error wrapping.
  - Three-tier permission architecture: `SAFE`, `CONTROLLED`, `DANGEROUS`.
  - **Tool Suite**:
    - `CalculatorTool` (`/calc`): Safe mathematical evaluator (AST parser with power-bomb limits).
    - `WebSearchTool` (`/search`): Instant internet search with structured titles, snippets, and clean URLs.
    - `BrowserTool` (`/browse`): Webpage fetcher and HTML text sanitizer.
    - `FilesystemTool` (`/file`): Directory-contained local file reader.
    - `ShellTool` (`/shell`): Permission-gated local command execution.
- **Model Abstraction (`victor/models/`)**:
  - Pluggable `BaseLLM` interface.
  - Native `OllamaProvider` connecting to local models (e.g. `qwen2:1.5b`, `qwen3.5:2b`) with automatic fallback and diagnostics.
  - `RemoteOpenAIProvider` for cloud or OpenAI-compatible endpoints (OpenAI, Groq, OpenRouter, LocalAI).
- **Independent Personality System (`config/victor.yaml`)**:
  - Decoupled persona configuration (curiosity, humor, formality, tone).
  - Dynamic prompt synthesis preserving Victor's identity regardless of model swaps.
- **Interactive Interfaces**:
  - **Terminal Command Center (`python -m victor.cli`)**: Rich styled REPL with streaming tokens, tool status chips, and command completion.
  - **Web Command Center (`python -m victor.api.server`)**: Dark futuristic command center with real-time WebSocket communication, live tool execution cards, tool dashboard, and responsive design.

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/your-username/victor.git
cd Victor_The_Artificial_Soul

# Install dependencies
pip install -r requirements.txt
```

### 2. Launch Interactive CLI

```bash
python -m victor.cli
```

### 3. Launch Dark Command-Center Web UI

```bash
python -m victor.api.server
```

Open your browser at: **`http://localhost:8000`**

---

## 💬 Usage Examples

### Direct Slash Commands
- `/calc sqrt(256) * 10 + 4`
- `/search compiler optimization advances`
- `/browse https://en.wikipedia.org/wiki/Artificial_intelligence`
- `/file config/victor.yaml`
- `/tools`
- `/help`

### Natural Language Autonomous Invocations
- *"What is 45 percent of 850?"*
- *"Can you search the web for the latest compiler news and tell me what you found?"*

---

## 🛡️ Security & Permissions

Victor enforces strict permission levels for all capabilities:
- **`SAFE`**: Read-only computations and web queries (`calculator`, `web_search`).
- **`CONTROLLED`**: Webpage browsing and sandboxed local file reading (`browser`, `filesystem`).
- **`DANGEROUS`**: Arbitrary command-line execution (`shell`). Disabled by default; requires explicit authorization (`allow_shell: true`) in `config/victor.yaml`.

---

## 🧪 Running Tests

```bash
python -m pytest -v tests/
```
