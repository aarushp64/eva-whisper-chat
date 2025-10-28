# Eva AI Agent - Quick Start Guide

## 🚀 Get Running in 5 Minutes

### Step 1: Install Ollama
```powershell
# Download and install from https://ollama.ai
# Then pull a model:
ollama pull llama3.2
```

### Step 2: Run Setup
```powershell
# From project root
.\scripts\setup.ps1
```

### Step 3: Start Services
```powershell
.\scripts\start-all.ps1
```

### Step 4: Test the Agent
Open browser to `http://localhost:5173` or test via API:

```powershell
# Test basic query
curl -X POST http://localhost:5000/api/agent/query `
  -H "Content-Type: application/json" `
  -d '{\"query\": \"Hello, who are you?\"}'

# Test calculator tool
curl -X POST http://localhost:5000/api/agent/query `
  -H "Content-Type: application/json" `
  -d '{\"query\": \"What is 156 * 23?\"}'

# Test web search
curl -X POST http://localhost:5000/api/agent/query `
  -H "Content-Type: application/json" `
  -d '{\"query\": \"Search for latest AI news\"}'
```

---

## 📋 What You've Built

### Core Features ✅
- ✅ **Local LLM** - Ollama integration with Llama 3.2
- ✅ **AI Agent** - Multi-step reasoning with tool execution
- ✅ **RAG System** - Vector database for memory and learning
- ✅ **Built-in Tools** - Web search, calculator, file reader, time
- ✅ **API** - RESTful endpoints for all agent functions
- ✅ **Docker** - Full containerization with Ollama

### Architecture
```
Frontend (React) → Backend (Flask) → Agent → LLM (Ollama)
                                    ↓
                                  Tools
                                    ↓
                              Vector DB (ChromaDB)
```

---

## 🎯 Key Files Created

### Core Agent System
```
packages/backend/server/core/
├── llm/
│   ├── base_llm.py          # LLM interface
│   └── ollama_client.py     # Ollama integration
├── rag/
│   ├── vector_store.py      # ChromaDB wrapper
│   └── rag_engine.py        # RAG logic
├── agent/
│   ├── agent.py             # Main agent
│   ├── tools.py             # Tool definitions
│   └── executor.py          # Tool execution
├── config.py                # Configuration
└── agent_factory.py         # Agent creation
```

### API Routes
```
routes/agent_routes.py       # Agent endpoints
```

### Documentation
```
docs/
├── SETUP.md                 # Detailed setup
└── PROJECT_SUMMARY.md       # Portfolio highlights
```

### Scripts
```
scripts/
├── setup.ps1                # Automated setup
├── start-backend.ps1        # Start backend
├── start-frontend.ps1       # Start frontend
└── start-all.ps1            # Start everything
```

---

## 🔧 Configuration

Edit `packages/backend/server/.env`:

```env
# LLM Settings
LLM_MODEL=llama3.2              # Change model here
OLLAMA_HOST=http://localhost:11434
LLM_TEMPERATURE=0.7             # 0 = deterministic, 1 = creative

# Agent Settings
AGENT_MAX_ITERATIONS=5          # Max reasoning steps
AGENT_ENABLE_TOOLS=true         # Enable/disable tools
AGENT_ENABLE_MEMORY=true        # Enable/disable learning

# RAG Settings
RAG_MAX_DOCS=5                  # Context documents to retrieve
RAG_SIMILARITY=0.7              # Similarity threshold (0-1)
```

---

## 🎨 Next Steps

### 1. Test Different Models
```bash
# Try Mistral (7B, more capable)
ollama pull mistral
# Update .env: LLM_MODEL=mistral

# Try CodeLlama (for coding tasks)
ollama pull codellama
# Update .env: LLM_MODEL=codellama
```

### 2. Add Custom Tools
Edit `packages/backend/server/core/agent/tools.py`:

```python
class MyTool(Tool):
    def __init__(self):
        super().__init__(
            name="my_tool",
            description="What it does",
            parameters=[...]
        )
    
    def execute(self, **kwargs):
        # Your logic
        return {'success': True, 'result': output}
```

Register in `core/agent_factory.py`:
```python
tool_registry.register(MyTool())
```

### 3. Customize System Prompt
Edit `packages/backend/server/core/agent/agent.py`:

```python
def _get_default_system_prompt(self) -> str:
    return """You are Eva, a specialized AI agent for [your domain].
    
    Your expertise includes:
    - [Skill 1]
    - [Skill 2]
    
    [Your custom instructions]
    """
```

### 4. Build Frontend UI
The frontend is already set up at `packages/frontend/`. You can:
- Add agent-specific components
- Show tool execution in real-time
- Display memory/knowledge base
- Add voice input interface

---

## 🐛 Troubleshooting

### Ollama Not Running
```powershell
# Check status
curl http://localhost:11434/api/tags

# Start Ollama (it should auto-start, but if not)
# Windows: Check system tray
# Linux: sudo systemctl start ollama
```

### Python Dependencies Error
```powershell
cd packages\backend\server
.\venv\Scripts\activate
pip install -r requirements.txt --force-reinstall
```

### Port Already in Use
```powershell
# Find process using port 5000
netstat -ano | findstr :5000

# Kill it
taskkill /PID <PID> /F
```

### ChromaDB Issues
```powershell
# Clear vector store
Remove-Item -Recurse -Force packages\backend\server\data\vector_store
```

---

## 📊 API Endpoints

### Agent
- `POST /api/agent/query` - Process query
- `GET /api/agent/stats` - Get statistics
- `GET /api/agent/tools` - List tools

### Legacy (from existing code)
- `POST /api/auth/register` - Register user
- `POST /api/auth/login` - Login
- `GET /api/chat/*` - Chat management
- `POST /api/speech/transcribe` - Speech to text

---

## 💡 Example Queries

Try these to see the agent in action:

```json
// Basic conversation
{"query": "Tell me about yourself"}

// Calculator tool
{"query": "Calculate the square root of 144"}

// Web search tool
{"query": "What are the latest developments in AI?"}

// File reader tool
{"query": "Read the file at ./README.md"}

// Current time tool
{"query": "What time is it?"}

// Multi-step reasoning
{"query": "Search for Python tutorials and calculate how many hours I need to study if each tutorial is 2.5 hours and I found 4 tutorials"}
```

---

## 🎓 Learning Resources

### Understanding the Code
1. Start with `core/agent_factory.py` - See how everything connects
2. Read `core/agent/agent.py` - Understand the reasoning loop
3. Check `core/llm/ollama_client.py` - See LLM integration
4. Explore `core/rag/rag_engine.py` - Learn about RAG

### Extending the Project
- Add more tools in `core/agent/tools.py`
- Implement new LLM providers in `core/llm/`
- Customize the agent behavior in `core/agent/agent.py`
- Build UI components in `packages/frontend/`

---

## 📞 Support

- **Documentation**: See `docs/SETUP.md` for detailed setup
- **Architecture**: See `docs/PROJECT_SUMMARY.md` for overview
- **Issues**: Check logs in `packages/backend/server/eva.log`

---

## 🎉 You're Ready!

Your AI agent is now running. Start experimenting with:
- Different models
- Custom tools
- System prompts
- Frontend integration

**Happy coding! 🚀**
