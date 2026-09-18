<div align="center">

# 🎙️ DataForge — Real-Time AI Voice Agent

### *A premium, real-time, agentic voice experience — built with free & open-source technologies.*

<br/>

![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=next.js&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue?logo=typescript&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-4-38bdf8?logo=tailwindcss&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Python-009688?logo=fastapi&logoColor=white)
![WebSockets](https://img.shields.io/badge/WebSockets-Realtime-4f9cf6?logo=websocket&logoColor=white)
![AssemblyAI](https://img.shields.io/badge/STT-AssemblyAI-111827?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdib3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0iI2ZmZiIgZD0iTTE3IDN2MThoLTJWNWgtMlYzaDR6TTkgM3YxOEg3VjVINVYzaDR6Ii8+PC9zdmc+)
![Status](https://img.shields.io/badge/Status-Early%20Development-8b5cf6)
![License](https://img.shields.io/badge/License-MIT%20(planned)-green)

<br/>

> **"Not another chatbot with a microphone. A real-time intelligent agent where
> voice is the primary interface."**

</div>

---

## 📑 Table of Contents

- [1. Project Overview](#1-project-overview)
- [2. Hackathon Information](#2-hackathon-information)
- [3. Problem Statement](#3-problem-statement)
- [4. Solution](#4-solution)
- [5. Why Voice?](#5-why-voice)
- [6. Key Features](#6-key-features)
- [7. Architecture](#7-architecture)
- [8. Voice Pipeline](#8-voice-pipeline)
- [9. Agent Logic](#9-agent-logic)
- [10. Tools / Function Calling](#10-tools--function-calling)
- [11. RAG (Knowledge Base)](#11-rag-knowledge-base)
- [12. Memory](#12-memory)
- [13. Technology Stack](#13-technology-stack)
- [14. UI / UX Design](#14-ui--ux-design)
- [15. Animation System](#15-animation-system)
- [16. Repository Structure](#16-repository-structure)
- [17. Installation](#17-installation)
- [18. Environment Variables](#18-environment-variables)
- [19. Local Development](#19-local-development)
- [20. API & WebSocket](#20-api--websocket)
- [21. Testing Strategy](#21-testing-strategy)
- [22. Security](#22-security)
- [23. Performance & Latency](#23-performance--latency)
- [24. Observability](#24-observability)
- [25. Development Roadmap (Sept 1–30, 2026)](#25-development-roadmap-sept-130-2026)
- [26. Hackathon Roadmap](#26-hackathon-roadmap)
- [27. Demo Scenario (2–3 min)](#27-demo-scenario-23-min)
- [28. Future Improvements](#28-future-improvements)
- [29. Team](#29-team)
- [30. License](#30-license)

---

## Status Legend

| Badge | Meaning |
| :---: | :--- |
| ✅ **IMPLEMENTED** | Confirmed present in the repository. |
| 🔨 **IN PROGRESS** | Actively being developed. |
| 🔮 **PLANNED** | Future work. Never presented as finished. |

> **Honesty rule:** this document clearly separates what exists from what is
> planned. Features marked 🔮 are *designed and scheduled* — not yet built.

---

## 1. Project Overview

**DataForge** is a real-time AI **Voice Agent** built during the
**AssemblyAI Voice Agent Hackathon** (September 2026). It combines:

- 🔴 **Real-time speech recognition** via AssemblyAI Universal-Streaming
- 🧠 **Agentic reasoning** (LLM + tools + memory + knowledge)
- 🎙️ **Premium voice-first UX** with live audio visualization and stateful mic UI
- ⚡ **Low-latency conversation loops** with turn detection and **barge-in** support

The product behaves like a real assistant: you *speak*, it *understands*,
*thinks*, answers, and can be **interrupted mid-sentence** — exactly like a
natural human conversation.

**Current status:** **Part 2 — AI Agent Core is implemented and verified.**
The voice pipeline works end-to-end in mock mode (no API key required) and is
wired for the real AssemblyAI Universal-Streaming API (`STT_MODE=real`) and the
real Groq free-tier LLM (`LLM_MODE=real`). Final transcripts now flow through a
session-aware agent that replies conversationally, remembers the conversation,
and renders the reply in the transcript panel. Tools, RAG, long-term memory and
TTS are 🔮 **PLANNED** for Parts 3–4.

| Part | Scope | Status |
| :--- | :--- | :--- |
| **Part 1** | System foundation: UI, mic, WebSocket relay, AssemblyAI streaming, transcript | ✅ IMPLEMENTED |
| **Part 2** | AI agent core: LLM integration, session memory, transcript → agent → reply | ✅ IMPLEMENTED |
| Part 3 | Voice experience: barge-in, streaming TTS, latency | 🔮 PLANNED |
| Part 4 | Tools / RAG, polish, deployment, demo & submission | 🔮 PLANNED |

---

## 2. Hackathon Information

| | |
| :--- | :--- |
| **Event** | AssemblyAI Voice Agent Hackathon |
| **Organizer** | lablab.ai × AssemblyAI |
| **Dates** | September 1–30, 2026 |
| **Theme** | Real-Time Voice Agents |
| **Repository** | [`Melainin2/DataForge`](https://github.com/Melainin2/DataForge) |

---

## 3. Problem Statement

Voice assistants are everywhere, yet most are:

- **Turn-based and sluggish** — "speak → wait 10 s → hear a reply · repeat".
- **Passive** — they answer but don't *reason*, *remember*, or *use tools*.
- **Ugly** — terminal-style UIs that never feel like a product.
- **Locked in** to expensive, opaque cloud stacks.

Building a voice agent that *feels alive* — sub-second understanding, real-time
mid-sentence interruption, memory, knowledge retrieval, and tool use — is
genuinely hard, and almost everyone reaches for costly platforms.

**We set out to prove this can be done beautifully and almost entirely for free.**

---

## 4. Solution

DataForge is a **single, coherent voice product**:

- **Browser** captures mic audio (Web Audio API) and renders a living audio
  visualization.
- **FastAPI** backend opens a WebSocket, streams audio to **AssemblyAI** for
  real-time transcription, and orchestrates the **agent**.
- The **agent** reasons over *memory + retrieved knowledge (RAG)*, calls
  **tools**, and streams an answer that is **turned into speech** (TTS) and
  streamed back.
- The **UI** reflects live agent states (`IDLE → LISTENING → THINKING →
  SPEAKING`) with premium glassmorphism styling and meaningful animations.

---

## 5. Why Voice?

1. **Latency hides complexity.** With < 1 s round-trip understanding, the
   agent *feels* intelligent even when it is fast rather than omniscient.
2. **Interruption is the killer feature.** The ability to say *"wait, actually
   …"* mid-answer is what separates a demoware demo from true agent UX.
3. **Voice is the interface.** On a 2-minute demo, speech instantly reads as
   "modern AI product" to a non-technical judge — no UI tour required.
4. **Multi-modal potential.** The same pipeline can later visualize answers,
   open dashboards, or drive the browser with a tool.

---

## 6. Key Features

| # | Feature | Status |
| :-: | :--- | :-: |
| 1 | Real-time streaming speech recognition — AssemblyAI v3 Universal-Streaming client (real + mock) | ✅ IMPLEMENTED |
| 2 | Voice WebSocket relay (browser ↔ FastAPI ↔ AssemblyAI) with validation & error codes | ✅ IMPLEMENTED |
| 3 | Browser microphone capture → 16 kHz PCM16 resampler → base64 streaming | ✅ IMPLEMENTED |
| 4 | Live partial/final transcript rendered in the conversation panel | ✅ IMPLEMENTED |
| 5 | Centralized voice state machine (`IDLE/LISTENING/PROCESSING/THINKING/SPEAKING/ERROR`) | ✅ IMPLEMENTED |
| 6 | WebSocket connection management (connect / reconnect / backoff / error) | ✅ IMPLEMENTED |
| 7 | Dark glassmorphism UI, live canvas waveform (reactive to mic), responsive layout | ✅ IMPLEMENTED |
| 8 | `.env`-based secrets, never in frontend; `.env.example` + `.gitignore` | ✅ IMPLEMENTED |
| 9 | Agentic loop: final transcript → LLM reply, with `PROCESSING`/`THINKING` states (Groq free tier, swappable provider) | ✅ IMPLEMENTED |
| 10 | Conversational memory (short-term, per session, bounded context; persistent long-term optional) | ✅ IMPLEMENTED |
| 11 | RAG knowledge base (ChromaDB + local embeddings) | 🔮 PLANNED |
| 12 | Turn detection & **barge-in / interruption handling** | 🔮 PLANNED |
| 13 | Streaming TTS back to the browser | 🔮 PLANNED |
| 14 | Latency observability per pipeline stage (transcript → agent → reply) | ✅ IMPLEMENTED |

---

## 7. Architecture

```mermaid
flowchart TD
    USER[👤 User]
    BROWSER[Browser — Next.js / Tailwind / Canvas waveform]

    subgraph BROWSER_APP[FRONTEND — Next.js + React]
        MIC[Microphone - Web Audio API]
        VIZ[Live Audio Visualization]
        VOICEUI[Voice State UI ✓🎙️]
    end

    subgraph BACKEND[BACKEND — FastAPI + WebSockets]
        WS[WebSocket Gateway]
        ORCH[Agent Orchestrator - LangGraph loop]
        TOOLS[Tools ✓ search / RAG / actions]
        RAG[ChromaDB + local embedder]
        LLM[LLM - fast streaming provider]
        MEM[Memory - LangGraph checkpointer - SQLite]
    end

    subgraph EXTERNAL[EXTERNAL SERVICES]
        AAI[🎧 AssemblyAI Universal Streaming]
        TTS[🗣 TTS Engine]
    end

    USER --> MIC
    MIC --> BROWSER
    BROWSER --> VIZ
    VOICEUI --> BROWSER

    BROWSER -- WebSocket audio + events --> WS
    WS --> ORCH
    ORCH <--> MEM
    ORCH --> TOOLS
    ORCH --> RAG
    ORCH --> LLM
    WS <--> AAI
    WS <--> TTS

    VIZ -. audio reactive .-> VOICEUI
    ORCH -- state events --> WS --> VOICEUI
```

**Key properties:** browser ↔ FastAPI over a single WebSocket; FastAPI ↔
AssemblyAI over a streaming bidirectional socket; agent decisions stay server-side
so keys never reach the client.

---

## 8. Voice Pipeline

```mermaid
sequenceDiagram
    participant U as User
    participant B as Browser
    participant F as FastAPI (WS)
    participant A as AssemblyAI Streaming
    participant AG as Agent (LangGraph)
    participant L as LLM
    participant T as TTS
    participant S as Speaker

    U->>B: speaks
    B->>F: mic PCM chunks (WebSocket)
    F->>A: forward audio frames
    A-->>F: partial transcripts (streaming)
    F->>AG: final transcript
    AG->>L: reasoning + tools + memory + RAG
    L-->>AG: streamed tokens
    AG->>T: text-to-speech request
    T-->>F: streamed audio
    F-->>B: streamed audio + state=SPEAKING
    B->>S: play TTS audio

    Note over B,F: ← BARGE-IN: user speaks during SPEAKING
    B->>F: interrupt event
    F-->>A: stop + restart stream
    F->>B: state=LISTENING
    AG->>AG: resume agent loop
```

**Turn detection** uses signal energy + AssemblyAI final/partial transcripts.
**Interruption** cancels current TTS playback client-side *and* terminates the
backend utterance so the agent re-enters `LISTENING`.

---

## 9. Agent Logic

The agent is a **graph-based loop** (LangGraph), fully controllable and
observable:

```mermaid
flowchart LR
    A([Start]) --> B{Raw input?}
    B -->|needs facts| C[/Retrieve from RAG/]
    B -->|needs action| D[/Call tool/]
    B -->|answerable| E[/Draft reply/]
    C --> F{Enough to answer?}
    D --> F
    F -->|no| G[/Ask follow-up or search again/]
    F -->|yes| E
    E --> H([Respond streamed])
```

Every step asks three questions:

1. *Can I answer directly from context?* → reply.
2. *Do I need external information?* → RAG retrieval.
3. *Do I need to execute an action?* → tool call.

The loop runs until `ANSWER` — no more tool calls — then hands the text to TTS.

---

## 10. Tools / Function Calling

| Tool | Purpose | Status |
| :--- | :--- | :--- |
| `search_web` | Current-info lookups via a free search endpoint | 🔮 PLANNED |
| `rag_search` | Query the knowledge base with the top-k context | 🔮 PLANNED |
| `lookup_docs` | Fetch a specific document/chunk from the KB | 🔮 PLANNED |
| `remember / forget` | Explicit memory writes for long-term memory | 🔮 PLANNED |

**Design rule:** tools are opt-in — the agent decides when to use them, keeping
the core loop lean and the latency low.

---

## 11. RAG (Knowledge Base)

```mermaid
flowchart TD
    D[Docs / domain data] --> P[Parser & chunker]
    P --> E[Embedder - local model]
    E --> V[(ChromaDB)]
    Q[User question] --> QV[Query embedder]
    QV --> V
    V --> R[Top-k relevant chunks]
    R --> L[LLM]
    L --> G[Grounded response]
```

| Layer | Choice | Why (free-first) |
| :--- | :--- | :--- |
| Vector DB | **ChromaDB** | Open-source, local, zero-infra, persistent |
| Embeddings | **fastembed / sentence-transformers** (`all-MiniLM-L6-v2`) | Local & free — no API cost |
| Chunking | Recursive text splitter (~500 tokens, 15% overlap) | Simple, deterministic |

The agent is instructed to answer **only from the retrieved context** and to
say "I don't have that information" when a question is out of scope →
**hallucination control**.

---

## 12. Memory

```mermaid
flowchart LR
    CONV[Current conversation] --> HIST[(Session history - checkpointer)]
    HIST --> CTX[Agent context window]
    CTX --> LLM[LLM]
    IMPL[Important facts] --> LTM[(Long-term memory - SQLite)]
    LTM --> CTX
```

- **Short-term memory:** automatic — the per-session conversation is stored in
  an in-memory `ConversationManager` (bounded to `MAX_CONTEXT_MESSAGES` turns)
  and re-injected on every agent turn. *Part 2 ships this; a persistent
  checkpointer (SQLite) is planned for Part 4.*
- **Long-term memory:** explicit facts ("user's name…", recurring preferences)
  persisted and recalled in later sessions. *(Optional, keeps MVP simple.)*

---

## 13. Technology Stack

All choices follow the **Technical Decision Principle**: *necessary? free/open
source? improves the product? reduces complexity? improves latency? improves
the demo?*

| Layer | Technology | Cost | Rationale |
| :--- | :--- | :--- | :--- |
| Frontend | **Next.js 15** + React + TypeScript | Free | App Router, streaming SSR, HMR |
| Styling | **Tailwind CSS** + shadcn/ui + Lucide icons | Free | Fast, consistent, professional |
| Motion | **Motion (Framer Motion)** | Free | Declarative, performant animations |
| Audio capture | **Web Audio API** (`getUserMedia`) | Free | Native, zero deps |
| Audio visualization | Canvas + `AnalyserNode` | Free | Lightweight, reactive to real audio |
| Real-time layer | **WebSocket** | Free | Bidirectional, low overhead |
| Backend | **Python + FastAPI** | Free | Async, Pydantic, WebSocket-first |
| Agent framework | **LangGraph** | Free | Graph agent loop + memory checkpoints |
| LLM | Fast streaming provider (**Groq free tier**, OpenAI-compatible) | Free tier | Very low latency, generous free tier |
| STT | **AssemblyAI Universal-Streaming API** | Free tier | The hackathon's core requirement |
| TTS | Free/open TTS engine (e.g. Piper, Edge-TTS) | Free | Streamed speech without cloud cost |
| RAG | **ChromaDB** + fastembed local model | Free | Local, persistent, no server |
| Database | **SQLite** (via checkpointer) — Postgres/Supabase if scale needed | Free | Zero-config for MVP |
| Deployment | **Vercel** (frontend) + **Render** (backend) | Free tier | Documented below |
| Observability | Lightweight structured logs + per-stage latency metrics | Free | No paid monitoring |

> ⚠️ **Free-tier disclaimer:** free tiers are generous but can change.
> Availability is verified *at the time of deployment* — nothing is claimed
> here as guaranteed.

---

## 14. UI / UX Design

**Direction: Modern · Minimal · Futuristic · Professional · Voice-centric.**

```text
┌────────────────────────────────────────────────────┐
│ ◉ DataForge                 ● ONLINE      [API]   │
├────────────────────────────────────────────────────┤
│                                                    │
│                    AI VOICE AGENT                  │
│                                                    │
│                      ◉                             │
│                 ╱────────╲      ← animated states  │
│                                                    │
│        ~~~~~ ~~~~~ ~~~~~ ~~~~~  ← live waveform    │
│                                                    │
│                     Listening…                     │
│                                                    │
├────────────────────────────────────────────────────┤
│ Transcript                                          │
│   User    "What's the current context…"            │
│   Agent   "Based on the knowledge base…"           │
└────────────────────────────────────────────────────┘
```

**Visual system**

- Dark futuristic theme with **glassmorphism** panels (frosted blur + subtle border).
- **Subtle gradient accents** (indigo/violet) — never loud.
- **Glowing microphone** whose halo and pulse reflect state.
- Elegant typography, generous spacing, restrained motion.
- Fully **responsive**: the mic stays reachable on mobile.

### Voice States

| State | Visual representation |
| :--- | :--- |
| `IDLE` | Minimal microphone, dim ambient pulse |
| `LISTENING` | Mic glow + live waveform reacts to input |
| `THINKING` | Subtle AI "orbit" indicator, waveform settles |
| `PROCESSING` | Soft pulsing ring, low-key shimmer |
| `SPEAKING` | Waveform reacts to *output* audio |
| `ERROR` | Smooth but obvious red/shimmer state |

---

## 15. Animation System

Animations are **meaningful and performant** — never decorative clutter.

| Category | Technique |
| :--- | :--- |
| Page entrance | Fade + slide with `Motion` |
| Voice activation | Mic scale + glow (CSS + Motion) |
| Audio activity | Canvas waveform driven by `AnalyserNode` |
| Thinking | Subtle orbiting indicator |
| Speaking | Reactive waveform |
| Transcript | Messages fade/slide in |
| State transitions | Cross-fade keyed by `agentState` |
| Errors | Gentle shake + tint, never seizure-inducing |

**Performance rule:** all animations run on `transform`/`opacity` (GPU-friendly),
and the waveform loop pauses when no audio is active.

---

## 16. Repository Structure

```text
DataForge/
├── README.md                 # this document
├── .env.example              # secrets template (no real values)
├── .gitignore
├── backend/                  # FastAPI app
│   ├── requirements.txt
│   ├── .env.example
│   ├── app/
│   │   ├── main.py           # app factory, CORS, router wiring, agent lifespan
│   │   ├── config.py         # pydantic-settings (env-based config, STT + LLM)
│   │   ├── agent/            # Part 2 — intelligence layer
│   │   │   ├── agent.py      # VoiceAgent.process(transcript, session_id)
│   │   │   ├── llm.py        # LLMProvider interface + Groq + deterministic mock
│   │   │   ├── memory.py     # conversation memory (session store, bounded)
│   │   │   ├── prompts.py    # voice-first system prompt + fallback reply
│   │   │   └── types.py      # Message / Conversation dataclasses
│   │   ├── api/
│   │   │   └── health.py     # GET /api/health (reports STT + LLM + agent status)
│   │   ├── ws/
│   │   │   └── router.py     # /ws/voice relay + agent turn orchestration
│   │   ├── services/
│   │   │   └── assemblyai.py # v3 streaming client (real + mock)
│   │   ├── models/
│   │   │   └── ws.py         # client message + outbound payload builders
│   │   └── utils/
│   │       └── logging.py
│   └── tests/                # pytest (health + WebSocket relay + agent unit/integration)
├── frontend/                 # Next.js app
│   ├── package.json
│   ├── next.config.mjs
│   ├── tsconfig.json
│   ├── postcss.config.mjs
│   ├── .env.example          # NEXT_PUBLIC_WS_URL only
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── globals.css       # Tailwind v4 + dark theme tokens
│   │   └── page.tsx          # voice agent page (client component)
│   ├── components/
│   │   ├── connection-badge.tsx
│   │   ├── mic-button.tsx     # stateful glowing mic
│   │   ├── waveform.tsx       # canvas analyser/level visualization
│   │   └── transcript-panel.tsx
│   ├── hooks/
│   │   ├── use-voice-session.ts  # WS lifecycle + reconnect + transcript merge
│   │   └── use-microphone.ts     # capture → 16 kHz PCM16 resampler
│   └── lib/
│       ├── types.ts          # shared WS/types + transcript model
│       ├── states.ts         # centralized voice state machine
│       ├── transcript.ts     # partial/final merge logic
│       └── audio.ts          # PCM16 → base64 encode
└── docs/
    └── architecture-diagram.md   # deeper dive (optional, not yet created)
```

> ✅ The structure above matches the current repository (tool/RAG/TTS folders
> will be added in Parts 3–4).

---

## 17. Installation

### Prerequisites

- Python **3.11+** (tested with 3.12)
- Node.js **20+** (LTS) and npm (tested with Node 26 / npm 11)
- A microphone (desktop or mobile browser)
- An AssemblyAI API key for real streaming — **not needed** for mock mode

### Steps

```bash
# 1. Clone
git clone git@github.com:Melainin2/DataForge.git
cd DataForge

# 2. Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env         # add your ASSEMBLYAI_API_KEY

# 3. Frontend
cd ../frontend
npm install
cp .env.example .env.local   # keep NEXT_PUBLIC_WS_URL default for local dev
```

---

## 18. Environment Variables

> `.env.example` — **never commit real secrets.** No key is ever placed in
> frontend code; the browser only talks to our backend.

```env
# --- AssemblyAI (real streaming) ---
ASSEMBLYAI_API_KEY=
ASSEMBLYAI_SPEECH_MODEL=universal-3-5-pro

# real -> stream to AssemblyAI (needs a key)
# mock -> deterministic fake transcripts, perfect for local dev/tests
STT_MODE=real

# --- LLM (Part 2) — Groq free tier ---
# real -> Groq chat completions (needs a GROQ_API_KEY from console.groq.com)
# mock -> deterministic fake agent replies, perfect for local dev/tests
LLM_MODE=real
LLM_PROVIDER=groq
GROQ_API_KEY=
LLM_MODEL=llama-3.3-70b-versatile
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=512
LLM_TIMEOUT_SECONDS=30
# Bounded conversation history sent to the LLM per turn (latency control).
MAX_CONTEXT_MESSAGES=24

# --- Server ---
FRONTEND_ORIGIN=http://localhost:3000
LOG_LEVEL=INFO

# --- Frontend (frontend/.env.local) ---
# NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws/voice
```

> ⚠️ **Mock mode:** `STT_MODE=mock LLM_MODE=mock` lets you run the *entire* voice
> agent (speech → transcript → agent reply → transcript) with **zero API
> keys**. Real mode only needs `ASSEMBLYAI_API_KEY` + `GROQ_API_KEY`. The mock
> LLM is deterministic and demonstrates session memory ("My name is Ahmed…").

---

## 19. Local Development

```bash
# Backend (mock STT + mock LLM — zero API keys, great for offline demos)
cd backend
source .venv/bin/activate
STT_MODE=mock LLM_MODE=mock uvicorn app.main:app --reload --port 8000

# Backend (real AssemblyAI streaming + real Groq LLM)
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000   # reads backend/.env

# Frontend
cd frontend
npm run dev
# open http://localhost:3000
```

Opening the page triggers the mic-consent flow, opens the WebSocket, and the
agent enters `LISTENING` on tap. Say something — partials stream in live,
finals resolve, the **agent replies**, and the whole conversation renders
below the mic. (In mock mode, stop the session to complete your turn — the
mock STT emits its final transcript on close.)

## 20. API & WebSocket

**WebSocket endpoint:** `ws://localhost:8000/ws/voice` (backend-local;
configured in the frontend via `NEXT_PUBLIC_WS_URL`)

| Direction | Message (JSON) | Purpose |
| :--- | :--- | :--- |
| Browser → Backend | `{"type":"start_session"}` | Open an AssemblyAI session, → `LISTENING` |
| Browser → Backend | `{"type":"audio","data":"<base64 pcm16>"}` | Stream mic audio (16 kHz mono) |
| Browser → Backend | `{"type":"stop_session"}` | Send `Terminate`, flush the final transcript |
| Browser → Backend | `{"type":"ping"}` | Keepalive → `pong` |
| Backend → Browser | `{"type":"connected","session_id":"..."}` | Relay established |
| Backend → Browser | `{"type":"state","state":"LISTENING"}` | Server-side voice state change |
| Backend → Browser | `{"type":"partial","text":"..."}` | Live (non-final) transcript |
| Backend → Browser | `{"type":"final","text":"..."}` | Final transcript (completed user turn) |
| Backend → Browser | `{"type":"agent_message","text":"..."}` | Agent's reply to the final transcript (Part 2) |
| Backend → Browser | `{"type":"session_closed"}` | STT session ended |
| Backend → Browser | `{"type":"error","code":"...","message":"..."}` | Recoverable errors |

**Lifecycle (Part 2):**
1. Browser opens the WebSocket; backend acks with `connected`.
2. Browser sends `start_session` → backend connects to the AssemblyAI
   Universal-Streaming socket (v3) → `state: LISTENING`.
3. Mic PCM (16 kHz PCM16, base64 frames) flows browser → backend → AssemblyAI.
4. AssemblyAI `Turn` messages are relayed as `partial` (end_of_turn=false) or
   `final` (end_of_turn=true).
5. On the **final** transcript the backend runs the Agent for this session
   (memory ← user turn → LLM → memory ← reply), driving the UI through
   `PROCESSING → THINKING`, then delivers `agent_message` and returns to
   `state: LISTENING`.
6. `stop_session` → backend sends `{"type":"Terminate"}` (flushes the final
   transcript), closes the session, returns to `state: IDLE`.

> Interrupt message (`interrupt`), tools, RAG, streaming and TTS messages are
> reserved for Parts 3–4 and intentionally not implemented yet.

---

## 21. Testing Strategy

| Layer | What we test | Tooling |
| :--- | :--- | :--- |
| Voice | mic permissions, silence, background noise, interruption | Manual checklist + `pytest` fixture scripts |
| STT | API contract, reconnect, partial/final events | Mocked AssemblyAI client |
| Agent | conversation memory/context, LLM error fallbacks, provider contract | `pytest` (deterministic mock LLM + httpx `MockTransport`) |
| RAG | retrieval quality, irrelevant/missing-info queries | Retrieval assertions on fixture docs |
| Backend | WebSocket errors, timeouts, reconnection | `pytest` + `httpx.ASGITransport`, `websockets` |
| UI | responsive, animations, a11y, loading states | Playwright + RTL |

---

## 22. Security

- Secrets live **only** in backend `.env`; AssemblyAI/LLM/TTS calls occur
  server-side.
- `.env.example` ships with placeholders; real `.env` is git-ignored.
- CORS restricted to the frontend origin.
- Input sanitization + transcript length limits to guard prompt-injection.
- No credit-card or UI login required for the MVP demo.

---

## 23. Performance & Latency

Latency budget targets (from mic to agent reply):

```mermaid
xychart-beta
    title "Target: Under 1.2 s end-to-end"
    x-axis ["STT","Agent","Retrieval","TTS"]
    y-axis "ms" 0 --> 1200
    bar [300, 250, 200, 200]
```

- **STT:** streaming partials arrive continuously — the agent can start reading
  intent from partial text.
- **Agent:** compact tool-graph; parallel RAG lookup; single-streamed LLM turn.
- **TTS:** streamed chunks — speech *starts* before generation completes.
- **Barge-in:** cancels playback instantly and resets to `LISTENING`.

**Rule:** no `await` on anything unnecessary; every rule-blocked response is
reported in the latency telemetry.

---

## 24. Observability

Lightweight, self-hosted, zero-cost:

- Per-stage latency counters emitted on every turn:
  `STT → agent → tool(s) → retrieval → TTS → total`.
- Structured JSON logs (`session_id`, stage, duration).
- Optional `/metrics` endpoint (Prometheus format) — **PLANNED**, only if time permits.
- Demo helper: a small "latency HUD" in the UI (dev-only) to *show* judges the
  pipeline working.

---

## 25. Development Roadmap (Sept 1–30, 2026)

> 🔮 Items are planned unless marked ✅. Statuses flip as work lands.

### WEEK 1 — MVP · *Goal: Working Voice Agent*

> ✅ **Parts 1 & 2 delivered** — the foundation and agent core below are
> implemented and tested.

- [x] Clean repository, init git, professional README
- [x] Verify architecture & document stack
- [x] AssemblyAI universal-streaming integration (v3 client, real + mock)
- [x] Microphone capture (Web Audio API → 16 kHz PCM16 resampler)
- [x] Real-time transcription streaming (partial + final relay)
- [x] Voice WebSocket relay with validation, states & error codes
- [x] Basic frontend (mic button, live waveform, transcript panel, connection badge)
- [x] **Basic LLM turn (Part 2) — final transcript → Groq/mock agent reply**
- [ ] Basic TTS response (Part 3)

### WEEK 2 — AGENT · *Goal: chatbot → agent*

- [x] Agent orchestration (`VoiceAgent` over a swappable `LLMProvider`)
- [x] Memory (session conversation manager, bounded context)
- [x] Error handling & context management (natural fallbacks, failure isolation)
- [ ] Tool calling (RAG search, web search)
- [ ] RAG ingest + retrieval pipeline
- [ ] Persistent (long-term) memory checkpointer

### WEEK 3 — VOICE EXPERIENCE · *Goal: feels like a real voice agent*

- [ ] Streaming response path
- [ ] Turn detection (energy + partials)
- [ ] **Barge-in / interruption**
- [ ] Latency optimization pass
- [ ] Live audio visualization (waveform)
- [ ] Voice states + animations
- [ ] Responsive UI

### WEEK 4 — POLISH & SUBMISSION · *Goal: hackathon-ready product*

- [ ] UI polish & performance
- [ ] Security review & secrets hygiene
- [ ] Testing sweep (voice + agent + RAG + backend + UI)
- [ ] Production deployment (Vercel + Render)
- [ ] Demo scenario & demo script
- [ ] Demo video (screen + narration)
- [ ] README + architecture diagrams final pass
- [ ] Final submission to lablab.ai

---

## 26. Hackathon Roadmap

- **Strategy:** demonstrate **voice + real-time + agentic reasoning + tools +
  knowledge + memory + natural interaction + beautiful UX** in one demo.
- **Differentiator:** barge-in interaction and live audio visualization —
  two things a plain chatbot cannot do.
- **Submission assets:** README, architecture docs, demo video, and a live
  deployable URL (free tiers).

---

## 27. Demo Scenario (2–3 min)

```text
0:00  — Problem: assistants that make you wait.
0:20  — Introduce DataForge: "a voice agent, not a chatbot."
0:30  — User speaks naturally, no wake word.
0:50  — Agent understands mid-sentence (partial transcript visible live).
1:10  — Agent answers from the knowledge base / calls a tool.
1:30  — User interrupts: "wait, actually…"
1:45  — Agent stops, re-listens, adapts.
2:00  — Another capability: long-term memory ("you asked me this yesterday").
2:30  — Technical architecture (30-second diagram walkthrough).
2:50  — Final value pitch.
```

The demo is designed to show the *voice value* visually — the waveform, the
states, the interruption — not just a wall of text.

---

## 28. Future Improvements

- Multi-language support (AssemblyAI language codes)
- Streaming LLM-before-final + word-level partials for near-zero latency
- Supabase Postgres for cross-session long-term memory at scale
- Auth + per-user memory profiles
- Multi-agent team (specialist sub-agents behind one entry point)
- PWA + browser push for mobile parity

---

## 29. Team

| Role | Person |
| :--- | :--- |
| *(to be completed)* | — |

---

## 30. License

**MIT (planned).** A license will be attached before public submission —
decisions are tracked as an issue in this repository.

---

<div align="center">

**DataForge — where voice is the interface.** 🎙️✨

[⬆ Back to top](#-dataforge--real-time-ai-voice-agent)

</div>