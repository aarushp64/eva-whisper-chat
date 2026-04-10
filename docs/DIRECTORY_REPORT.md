# EVA — Directory Structure Report

**Generated:** 2026-04-09  
**Status:** ✅ Cleaned & verified — all imports pass, TypeScript zero errors

---

## What Was Removed

| File/Dir | Reason |
|---|---|
| `src/ai/providers/openrouter.js` | ❌ Deleted — unused provider, no configured key |
| `src/ai/providers/anthropic.js` | ❌ Deleted — unused provider, no configured key |
| `cache/` | ❌ Deleted — empty directory |
| `exports/` | ❌ Deleted — empty directory |
| `.env` — 12 lines of dead keys | ❌ Removed: OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY, COHERE_API_KEY, AZURE_OPENAI_API_KEY, OPENROUTER_API_KEY, PINECONE_API_KEY, SERPAPI_KEY, ELEVENLABS_API_KEY |
| `docker-compose.yml` — 4 unused services | ❌ Removed: postgres, mongo, node-backend (none actively used) |
| `docker-compose.yml` — hardcoded secrets | ❌ Removed: SECRET_KEY, JWT_SECRET_KEY, POSTGRES_PASSWORD |

---

## What Remains (Active Stack)

### Backend — Node.js (`server.js` + `src/ai/`)
This is the **primary AI pipeline** — the active agent path for chat.

```
packages/backend/server/
├── server.js                          # Express + Socket.IO entry point
├── .env                               # Runtime config (Groq + Ollama only)
├── .env.example                       # Template for new installs
│
├── src/ai/                            # 🧠 Agentic AI Core
│   ├── index.js                       # Barrel export (single import point)
│   ├── router.js                      # Model routing: Groq ↔ Ollama with fallback
│   ├── intent.js                      # Keyword-based intent detection
│   ├── memory.js                      # Rolling conversation memory
│   │
│   ├── providers/
│   │   ├── groq.js                    # ⚡ Groq SDK (streaming + non-streaming)
│   │   └── ollama.js                  # 🔒 Local Ollama API client
│   │
│   ├── agent/
│   │   ├── agent.js                   # Orchestrator: intent → planner → executor
│   │   ├── planner.js                 # LLM-based task decomposition
│   │   └── executor.js               # Step execution with tool matching
│   │
│   └── tools/
│       ├── index.js                   # Tool registry
│       ├── fileTool.js                # read_file, write_file
│       ├── shellTool.js               # run_command (with timeout cap)
│       ├── searchTool.js              # search_files by name pattern
│       └── webTool.js                 # fetch_url (HTML → text)
│
├── controllers/                       # Node.js controllers (used by server.js)
│   ├── messageController.js           # ✅ Active — handles socket messages
│   ├── authController.js              # ✅ Active — auth routes
│   ├── chatController.js              # ✅ Active — chat routes
│   ├── groupController.js             # ✅ Active — group routes
│   └── userController.js              # ✅ Active — user routes
│
├── routes/                            # Node.js route definitions
│   ├── auth.js                        # ✅ Registered in server.js
│   ├── chat.js                        # ✅ Registered in server.js
│   ├── user.js                        # ✅ Registered in server.js
│   └── group.js                       # ✅ Registered in server.js
│
├── models/                            # Mongoose (MongoDB) schemas
│   ├── User.js, Chat.js, Message.js   # ✅ Used by controllers
│   ├── Group.js, GroupMember.js       # ✅ Used by group controller
│   └── UserPreference.js              # ✅ Used by message controller
│
├── middleware/
│   └── auth.js                        # JWT verification for REST routes
│
├── utils/
│   ├── responseGenerator.js           # ✅ Bridges messageController → AI agent
│   ├── sentimentAnalysis.js           # ✅ Used by response generator
│   ├── userProfiling.js               # ✅ Used by message controller
│   └── memoryManager.js               # ✅ Used by message controller
```

### Backend — Python (`app.py`)
This is the **Flask server** — used for advanced features (RAG, Whisper, analytics).

```
packages/backend/server/
├── app.py                             # Flask + Socket.IO entry point
├── requirements.txt                   # Python dependencies
│
├── core/                              # 🧠 Python AI Agent (alternative path)
│   ├── agent_factory.py               # Creates Python Agent instances
│   ├── config.py                      # Env-driven config (LLM, RAG, Whisper)
│   ├── agent/                         # Python agent: LLM + RAG + tools
│   ├── llm/                           # Ollama client + stub fallback
│   └── rag/                           # ChromaDB vector store + RAG engine
│
├── routes/                            # Flask blueprints (registered in app.py)
│   ├── agent_routes.py                # /api/agent/query, /stats, /tools
│   ├── auth_routes.py                 # /api/auth/*
│   ├── chat_routes.py                 # /api/chat/*
│   ├── file_routes.py                 # /api/file/upload
│   ├── speech_routes.py               # /api/speech/transcribe
│   └── group_routes.py                # /api/group/*
│
├── controllers/                       # Python route handlers
│   ├── auth_controller.py             # ✅ Register, login, password reset
│   ├── chat_controller.py             # ✅ Chat CRUD + sentiment
│   ├── file_controller.py             # ✅ File upload
│   ├── group_controller.py            # ✅ Group management
│   ├── message_controller.py          # ✅ Message CRUD
│   ├── speech_controller.py           # ✅ Speech command processing
│   └── user_controller.py             # ✅ User profile + memory
│
├── models/                            # SQLAlchemy schemas
│   ├── db.py                          # DB initialization
│   ├── user.py, chat.py, message.py   # ✅ Used by Flask routes
│   ├── group.py, group_member.py      # ✅ Used by group controller
│   └── user_preference.py             # ✅ Memorized details + topics
│
├── speech/
│   ├── speech_processor.py            # Whisper STT + ElevenLabs TTS
│   └── speech_integration.py          # Base64 audio handling
│
├── memory/                            # Python-side memory managers
│   ├── memory_manager.py              # Hierarchical + conversation memory
│   ├── conversation_memory.py         # Short-term conversation tracking
│   └── hierarchical_memory.py         # Long-term structured memory
│
├── analytics/                         # Feature-flagged analytics
│   ├── data_processor.py              # Stats & data analysis
│   ├── ml_processor.py                # ML predictions
│   └── user_personalization.py        # Adaptive user modeling
│
├── nlp/                               # Feature-flagged NLP pipeline
│   ├── sentiment_analysis.py          # Sentiment + emotion detection
│   ├── intent_recognition.py          # Intent classification
│   ├── entity_recognition.py          # Named entity extraction
│   ├── entity_recognition_advanced.py # Context-aware NER
│   ├── intent_recognition_advanced.py # Multi-intent detection
│   ├── text_summarization.py          # Extractive summarization
│   ├── language_translation.py        # Translation support
│   └── question_answering.py          # QA pipeline
│
├── database/
│   ├── db_manager.py                  # Multi-DB manager (SQLite/Postgres/MySQL)
│   └── schema.py                      # Schema definitions
│
├── config/
│   └── advanced_features.py           # Feature flags + module configs
│
├── web_integration/
│   └── web_search.py                  # SERPAPI + DuckDuckGo search
│
├── utils/
│   ├── response_generator.py          # Fallback LLM responses (sentiment-based)
│   ├── advanced_response_generator.py # Multi-provider response generation
│   ├── sentiment_analysis.py          # Node.js sentiment (JS-side)
│   ├── user_profiling.py              # Node.js user profiling
│   ├── memory_manager.py              # Node.js memory utils
│   └── memoryManager.js               # JS memory helpers
│
├── data/                              # Runtime data (gitignored)
│   └── db/eva.db                      # SQLite database
├── uploads/                           # File uploads (gitignored)
├── instance/                          # Flask instance data (gitignored)
│
└── tests/                             # Python test suite
    ├── conftest.py
    ├── test_agent_routes.py
    ├── test_auth.py
    └── test_demo.py
```

### Frontend (React + TypeScript)
```
packages/frontend/
├── src/
│   ├── App.tsx                        # Root: routing + providers
│   ├── main.tsx                       # Entry point
│   ├── index.css                      # Tailwind + custom theme
│   │
│   ├── pages/
│   │   ├── Index.tsx                  # Main page: Sidebar + ChatWindow
│   │   └── NotFound.tsx               # 404 fallback
│   │
│   ├── components/
│   │   ├── chat/
│   │   │   ├── ChatWindow.tsx         # ✅ Main chat UI + LLM config badge
│   │   │   ├── LLMSettingsModal.tsx   # ⚙️ Provider/model selector dialog
│   │   │   ├── Sidebar.tsx            # Conversation list
│   │   │   └── AudioRecorder.tsx      # Voice recording
│   │   │
│   │   └── ui/                        # shadcn/ui components (51 files)
│   │       └── TypingIndicator.tsx    # Agent typing animation
│   │
│   ├── hooks/                         # React hooks
│   └── lib/utils.ts                   # cn() class merging
```

### Infrastructure
```
├── docker-compose.yml                 # Ollama + Python backend only
├── scripts/
│   ├── setup.ps1                      # Automated Windows setup
│   ├── start-all.ps1                  # Start all services
│   ├── start-backend.ps1              # Start Flask backend
│   └── start-frontend.ps1             # Start React frontend
└── docs/
    ├── SETUP.md                       # Detailed setup guide
    └── PROJECT_SUMMARY.md             # Portfolio overview
```

---

## Dual-Backend Architecture Note

This project runs **two backends simultaneously**:

| Backend | Entry | Language | Purpose |
|---|---|---|---|
| **Node.js** | `server.js` | JavaScript | Real-time chat via Socket.IO, MongoDB, JS agent pipeline |
| **Python (Flask)** | `app.py` | Python | REST API, RAG/ChromaDB, Whisper, SQLAlchemy, advanced NLP |

The **frontend currently connects to Node.js via Socket.IO** (port 8081). The Python Flask server (port 5000) serves the REST API (`/api/agent/*`, `/api/auth/*`, etc.) and is accessed for specific features.

The `src/ai/` pipeline (JS) flows: `ChatWindow → socket.emit → messageController → responseGenerator → runAssistant → routePrompt → Groq/Ollama`

---

## Security Status

| Item | Status |
|---|---|
| Exposed API keys in `.env` | ✅ **CLEANED** — all live keys removed |
| `.env` in `.gitignore` | ✅ Confirmed |
| API keys in source code | ✅ None found |
| `sessionStorage` for LLM config | ✅ Only provider + model (no API key) |
| API key per-request only | ✅ Key lives in React state → socket → backend → discarded |
| Docker hardcoded secrets | ✅ Replaced with `env_file` reference |

---

## Active Provider Chain

```
User selects: Groq (cloud) or Ollama (local) via ⚙️ LLM/API button
                    ↓
            sessionStorage {provider, model}
                    ↓
        ChatWindow sends llmConfig via socket
                    ↓
    ┌───────────────────────────────────────┐
    │  routePrompt(messages, llmConfig)     │
    │                                       │
    │  If Groq selected + API key present:  │
    │    → callGroq(messages, {apiKey})     │
    │    → fallback: callOllama(messages)   │
    │                                       │
    │  If Ollama selected:                  │
    │    → callOllama(messages)             │
    │    → fallback: none needed (local)    │
    └───────────────────────────────────────┘
```
