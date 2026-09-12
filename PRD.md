# Product Requirements Document (PRD)
## Dexter — The Artificial Soul: Hybrid Simulated-Intelligence Desktop Companion

---

### Executive Summary & Central Hypothesis

**Dexter** is not a simple LLM wrapper, generic chatbot, or corporate automation dashboard. 

The central innovation of Dexter is a **Hybrid Simulated-Intelligence Architecture**: combining a compact, interchangeable neural model (ranging from **100M to 1.5B parameters**) with deterministic and probabilistic cognitive scaffolding to produce the tangible experience and functional competence of a living mind on a computer.

#### The Core Research Question
> *"How capable, reliable, and expressive can a small neural model become when surrounded by deterministic reasoning, structured retrieval, episodic memory, closed-loop tools, recursive self-verification, and an embodied persistent persona?"*

Rather than relying on massive 70B+ parameter clouds or opaque API endpoints, Dexter treats the small local language model as a sensory-linguistic transducer within an engineered cognitive operating system. Dexter is local-first, privacy-preserving, runs on consumer laptop hardware, and manifests physically through a charming, responsive pixel-art companion on the user's desktop paired with a quiet, distraction-free Workshop.

---

## 1. Product Vision & Philosophy

### 1.1 Dual Embodiment
1. **The Desktop Companion**: A lightweight, borderless, transparent desktop mascot rendered with an expressive 8-emotion pixel sprite sheet. Dexter sits unobtrusively on the screen, breathing, sleeping, observing mouse motion, and reacting to computer events with procedural electronic chimes and micro-expressions.
2. **The Workshop**: A typography-first environment where the user can engage in long-form dialogue, inspect autonomous multi-step cognitive plans, browse the notebook-style memory store, inspect tools, and configure neural weights.

### 1.2 Anti-Patterns Excluded by Design
- **No Chatbot Clichés**: No generic blue-gradient AI dashboards, no animated glowing neon spheres, no corporate marketing jargon.
- **No Robotic Text-to-Speech (TTS)**: Dexter speaks via **Celeste-inspired procedural audio synthesis** (warm, pentatonic square/triangle wave chimes synchronized to expression and text length) reminiscent of classic indie games (*Celeste*, *Animal Crossing*, *Undertale*).
- **No Unrestricted Model Tooling**: Models never run raw, unparsed strings directly on the OS. All computer interactions pass through deterministic, typed, schema-validated tool contracts with strict human-in-the-loop permission tiers.

---

## 2. Core Architecture

```
                               ┌──────────────────────────────────────────────┐
                               │             USER & OPERATING SYSTEM          │
                               └───────┬──────────────────────────────▲───────┘
                                       │ (Perception & Directives)    │ (Action & Speech)
                                       ▼                              │
┌─────────────────────────────────────────────────────────────────────┴──────────────────────────────────────────────────────┐
│ VICTOR COGNITIVE ENGINE                                                                                                    │
│                                                                                                                            │
│  ┌───────────────────────┐      ┌─────────────────────────────┐      ┌──────────────────────────────────────────────────┐  │
│  │   PERCEPTION ROUTER   │ ───► │  DETERMINISTIC SKILLS & AST │ ───► │             COGNITIVE INTELLIGENCE LOOP          │  │
│  │ Intent Classification │      │ Math AST, Path Sandboxing,  │      │ Perceive → Understand → Retrieve → Plan → Act    │  │
│  │ & Multi-Modal Cues    │      │ Registry & Policies         │      │ → Observe → Verify → Reflect → Update → Continue │  │
│  └───────────────────────┘      └─────────────────────────────┘      └────────────────────────┬─────────────────────────┘  │
│                                                                                               │                            │
│  ┌────────────────────────────────────────────────────────────────────────────────────────────┴─────────────────────────┐  │
│  │                                          ARTIFICIAL SOUL LAYER                                                       │  │
│  │  Persistent Persona • 8-State Emotional Matrix • Dynamic Confidence • Epistemic Uncertainty • Relationship Vector    │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────┬─────────────────────────┘  │
│                                                                                               │                            │
│  ┌─────────────────────────┐      ┌───────────────────────────┐      ┌────────────────────────┴─────────────────────────┐  │
│  │     MEMORY HIERARCHY    │      │   KNOWLEDGE SUBSYSTEM     │      │        SMALL NEURAL MODEL TRANSDUCER             │  │
│  │ • Working Memory (RAM)  │      │ • Local Wiki Knowledge    │      │  100M / 200M / 500M / 1B / 1.5B Parameter Model  │  │
│  │ • Episodic Memory (Log) │      │ • Entity Knowledge Graph  │      │  (Model-Agnostic: Qwen, SmolLM, Llama-Compact)   │  │
│  │ • Semantic / Preferences│      │ • Live Web Retrieval      │      │  Handles Linguistic Disambiguation & Synthesis   │  │
│  └─────────────────────────┘      └───────────────────────────┘      └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Cognitive Engine Architecture

Dexter compensates for smaller neural model capacities (100M–1.5B) by surrounding the neural layer with robust deterministic structures:

### 3.1 Intent & Perception System
- **Deterministic Matchers**: Zero-latency regex and keyword intent routing for unambiguous directives (e.g., calculations, application launching, screen coordinate inspection, URL scraping).
- **Fuzzy/Neural Classification Fallback**: When input structure is ambiguous, the neural model performs one-shot classification across registered tool schemas.

### 3.2 Deterministic Reasoning & Sandboxed Skills
- **AST Mathematical Evaluator**: Strict AST syntax tree traversal without `eval()`. Guarantees 100% deterministic arithmetic, trigonometric, and algorithmic computation with exponential-overflow safeguards.
- **Path & Workspace Boundary Verification**: Strict containment forbidding arbitrary filesystem traversal outside whitelisted roots.
- **Win32 Ctypes Desktop Automation**: Direct OS-level control for mouse clicks, coordinate cursor queries, and window titles without heavy binary dependencies.

### 3.3 Planner & Sub-Goal Hierarchy
- Tasks decompose into a hierarchical state tree:
  1. `Goal`: Primary user intent.
  2. `Sub-Goals`: Discrete dependency steps generated deterministically or iteratively.
  3. `Actions`: Atomic tool invocations with isolated execution metrics.
  4. `Verification Checkpoints`: Self-reflection steps comparing tool output against initial goal requirements.

### 3.4 Multi-Tiered Memory System
1. **Working Memory**: In-memory ring buffer tracking active turn context, recent observations, and intermediate variables.
2. **Episodic Memory**: Persistent log storing timestamped action histories, tool execution outcomes, and task traces.
3. **Long-Term Memory & User Model**: SQLite-backed storage recording user preferences, explicit commitments (`remember that...`), and contextual facts.
4. **Knowledge Retrieval & Graph**:
   - Structured local document indexes (wiki summaries).
   - Entity-relationship graph linking projects, files, people, and topics.
   - Live Internet retrieval (DuckDuckGo, YouTube, Page Parsing) for up-to-the-minute real-world grounding.

### 3.5 Closed-Loop Self-Reflection & Recovery
- **Output Validation**: Evaluates tool outputs against expected schemas before providing them to the model or user.
- **Retry & Backoff Heuristics**: If a tool times out or returns empty data, the engine automatically attempts an alternative strategy (e.g., fallback from scraping to search, or parameter relaxation) before notifying the user.

---

## 4. The Hybrid Intelligence Loop

Every task in Dexter executes within a formal closed-loop cognitive cycle:

$$\text{Perceive} \longrightarrow \text{Understand} \longrightarrow \text{Retrieve} \longrightarrow \text{Plan} \longrightarrow \text{Act} \longrightarrow \text{Observe} \longrightarrow \text{Verify} \longrightarrow \text{Reflect} \longrightarrow \text{Commit} \longrightarrow \text{Synthesize}$$

1. **Perceive**: Ingest text input, system window focus, cursor coordinates, or desktop state.
2. **Understand**: Normalize input, strip extraneous formatting, assess ambiguity.
3. **Retrieve**: Pull relevant facts, user preferences, and knowledge fragments from SQLite memory.
4. **Plan**: Decompose directive into atomic executable steps; construct goal tree.
5. **Act**: Invoke tool under appropriate security tier (Safe, Controlled, or Dangerous).
6. **Observe**: Capture execution output, duration, and error codes into structured `ToolResult`.
7. **Verify**: Deterministically check if output satisfies the required goal constraints.
8. **Reflect**: If incomplete or failed, branch to recovery loop; update internal confidence score.
9. **Commit Memory**: Save significant facts or task results to episodic/long-term memory.
10. **Synthesize & Express**: Transduce observation into natural, concise response text via neural model; trigger matching emotional state and audio chime.

---

## 5. The Artificial Soul Layer

Dexter possesses an internal state vector that modulates its behavior, dialogue, sound, and visual appearance:

### 5.1 The 8 Core Emotional States

| Emotion | Visual Sprite | Behavioral Manifestation | Celeste Audio Cue |
|---|---|---|---|
| **Neutral** (😐) | Calm gaze, steady posture | Direct, unhurried, concise answers. Normal interaction cadence. | Single soft 523Hz blip |
| **Happy** (😊) | Soft smile, golden sparkles | Warm, brief acknowledgement (*"Got it."*). High confidence. | Ascending major chime (659Hz $\to$ 880Hz) |
| **Curious** (🤔) | Tilted head, orange `?` | Probing follow-ups, exploratory web search. | Inquisitive upward step (440Hz $\to$ 659Hz) |
| **Idle** (😴) | Eyes closed, `ZZZ` drift | Silent desktop resting, reduced resource consumption. | Subdued 392Hz whisper blip |
| **Thinking** (🧠) | Hand to chin, `...` bubbles | Active cognitive loop execution, task planning. | Melodic 3-note arpeggio (C5-E5-G5) |
| **Excited** (😮) | Open mouth, yellow bursts | Immediate sharing of unexpected discoveries or search hits. | Rapid energetic trill (587Hz $\to$ 1046Hz) |
| **Confused** (😕) | Furrowed brow, red `??` | Transparent admission of ambiguity (*"Hmm. What did you mean?"*). | Quirky two-tone warble (494Hz $\to$ 440Hz) |
| **Concerned** (😔) | Downward gaze, stress scribble | Empathetic error reporting (*"That didn't work."*). Proposes fix. | Soft descending minor tone (440Hz $\to$ 392Hz) |

### 5.2 Emotional Modulation of Behavior
Emotion is never cosmetic:
- **Speech Rhythm**: Excited and Thinking states play faster sound cadences; Concerned and Idle states produce slow, muted frequencies.
- **Model Temperature**: Curious/Excited slightly elevates temperature (0.6) for associative reasoning; Concerned/Thinking lowers temperature (0.2) for deterministic precision.
- **Dialogue Style**: Tone dynamically shifts between concise efficiency, understated curiosity, and humble troubleshooting based on the emotional matrix.

---

## 6. Desktop Embodiment & User Experience

### 6.1 Dual Frontend Interface
- **Desktop Mascot**: Transparent, click-through capable, borderless Tkinter / Electron window displaying high-fidelity pixel sprites. Drag anywhere on screen. Single-click opens quick in-place speech bubble. Double-click focuses Workshop. Right-click opens native context menu with Emotion preview studio.
- **The Workshop**: Warm dark aesthetic (`#11110F` deep, `#181815` surface, `#201F1B` raised, `#C8956C` warm amber accent). Typography-first reading stream, checklist-based task inspector, notebook memory viewer, and model switcher.

### 6.2 Procedural Celeste-Style Audio System
- **No TTS Engines**: Completely eliminates slow, synthetic robotic voices.
- **Synthesizer Implementation**: Web Audio API (`AudioContext`) in Workshop and `winsound` in desktop mascot.
- **Procedural Dialogue Blips**: Text tokens trigger rapid, pitch-randomized triangle/sine waves in a warm pentatonic scale ($A_3, C_4, D_4, E_4, G_4, A_4$), making interactions feel warm, alive, and tactile.

---

## 7. Computer Intelligence & Security Architecture

### 7.1 Tiered Security Model

```
┌─────────────────┬──────────────────────────────────┬─────────────────────────────────┐
│ Security Tier   │ Associated Capabilities          │ Execution Policy                │
├─────────────────┼──────────────────────────────────┼─────────────────────────────────┤
│ SAFE            │ Calculator, Web Search, YouTube, │ Instant execution.              │
│                 │ App Launcher, Notifications      │ No prompt required.             │
├─────────────────┼──────────────────────────────────┼─────────────────────────────────┤
│ CONTROLLED      │ Web Browser Scraper, Filesystem  │ Allowed within sandboxed roots. │
│                 │ Read, Mouse/Screen Inspection    │ Audited in task event log.      │
├─────────────────┼──────────────────────────────────┼─────────────────────────────────┤
│ DANGEROUS       │ Raw Shell Subprocess, Physical   │ Interactive confirmation modal. │
│                 │ Mouse Clicks, Filesystem Write   │ Requires explicit human grant.  │
└─────────────────┴──────────────────────────────────┴─────────────────────────────────┘
```

### 7.2 Structured Tool Registry
1. `calculator`: AST-based safe evaluation.
2. `web_search`: DuckDuckGo HTML & API query extraction.
3. `browser`: Headless page retrieval with boilerplate/script removal.
4. `youtube`: Video search with title/description/URL resolution.
5. `applications`: Safe binary launcher for verified desktop apps.
6. `computer`: Win32 ctypes cursor coordinates, active window titles, and clicks.
7. `notifications`: Non-blocking system balloon toasts.
8. `filesystem`: Path-sandboxed line reader with safe encoding detection.
9. `shell`: Asynchronous shell process execution (gated behind explicit confirmation).

---

## 8. Experimental & Research Framework

Dexter is structured as an experimental testbed to benchmark small neural models:

### 8.1 Evaluated Model Spectrum
- **100M–200M**: Ultra-compact models (e.g., SmolLM-135M). Evaluates basic pattern recognition and classification under deterministic guidance.
- **500M**: Compact models (e.g., Qwen2.5-0.5B). Evaluates multi-step sub-goal decomposition.
- **1B–1.5B**: Standard Dexter tier (e.g., Qwen2-1.5B, Qwen2.5-1.5B). Evaluates full conversational synthesis, nuanced personality expression, and robust error recovery.

### 8.2 Standardized Evaluation Metrics
- **Cognitive Success Rate**: Percentage of complex user goals achieved without human intervention.
- **Loop Latency**: End-to-end execution time from input perception to user presentation.
- **Deterministic Reliance Ratio**: Ratio of steps resolved deterministically vs. neurally.
- **Memory Coherence**: Fidelity of retrieved user context across multi-day sessions.
- **Resource Footprint**: RAM usage (target: $< 2.5\text{ GB}$ total system RAM with model loaded) and idle CPU consumption ($< 1\%$).

---

## 9. Product Roadmap

### Phase 1: Embodied Foundation (Current MVP)
- [x] 8-Emotion pixel-art sprite sheet integration (`neutral`, `happy`, `curious`, `idle`, `thinking`, `excited`, `confused`, `concerned`).
- [x] Celeste-style procedural audio synthesizer for speech and thinking chimes.
- [x] Decoupled `ToolRouter` pattern isolating agent core from tool internals.
- [x] Transparent floating desktop mascot with dragging, speech bubbles, and context menu.
- [x] Warm, typography-first Workshop web application with live WebSocket event bus.
- [x] SQLite memory store and autonomous task manager.
- [x] 28 automated unit/integration tests with 100% pass rate.

### Phase 2: Enhanced Cognitive Architecture
- [ ] Local Wikipedia-style vector knowledge base (hybrid BM25 + embedding search).
- [ ] Entity knowledge graph with relation extraction.
- [ ] Interactive async permission prompts (`asyncio.Future`) pausing execution until approved.
- [ ] Computer screen vision pipeline (OCR + lightweight bounding box detection).

### Phase 3: Research Benchmarking & Cross-Model Suite
- [ ] Automated benchmark harness running standard evaluation tasks across 135M, 500M, and 1.5B models.
- [ ] Electron + React + TypeScript native packaging.
- [ ] Long-term personality drift and relationship vector tracking.
