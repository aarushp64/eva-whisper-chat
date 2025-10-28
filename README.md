# Eva - AI Agent with Local LLM

> **Portfolio-Ready AI Agent**: Self-hosted, intelligent assistant with tool execution, memory, and voice capabilities.

## 🎯 Overview

Eva is an advanced AI agent platform that runs entirely locally using Ollama. Unlike simple chatbots, Eva can:
- **Execute Tools**: Search the web, read files, perform calculations, and more
- **Learn & Remember**: Uses RAG (Retrieval Augmented Generation) to learn from interactions
- **Reason & Plan**: Multi-step reasoning to solve complex tasks
- **Voice Interaction**: Speech-to-text with Whisper (coming soon)
- **Self-Hosted**: Complete privacy with local LLM inference

## ✨ Key Features

### 🤖 AI Agent Capabilities
- **Tool Execution**: Web search, file operations, calculations, time queries
- **Multi-Step Reasoning**: Breaks down complex tasks into steps
- **Autonomous Decision Making**: Decides when and which tools to use
- **Error Recovery**: Handles failures gracefully and retries

### 🧠 Memory & Learning (RAG)
- **Vector Database**: ChromaDB for semantic search
- **Conversation Memory**: Learns from every interaction
- **Context Retrieval**: Finds relevant past conversations
- **Knowledge Base**: Build domain-specific knowledge over time

### 💬 Local LLM Integration
- **Ollama Support**: Run Llama 3.2, Mistral, CodeLlama, and more
- **Streaming Responses**: Real-time token generation
- **Configurable Models**: Easy model switching
- **Privacy First**: All inference happens locally

### 🎙️ Speech Processing (In Progress)
- **Whisper Integration**: OpenAI Whisper for speech-to-text
- **Multi-Language Support**: Transcribe in multiple languages
- **Voice Commands**: Control Eva with your voice

### 🔧 Built-In Tools
- **Web Search**: DuckDuckGo integration for real-time information
- **File Reader**: Read and analyze local files
- **Calculator**: Safe mathematical expression evaluation
- **Time/Date**: Current time and date information
- **Extensible**: Easy to add custom tools

## 🏗️ Architecture

```
eva-whisper-chat/
├── packages/
│   ├── backend/
│   │   └── server/
│   │       ├── core/              # 🆕 AI Agent Core
│   │       │   ├── agent/         # Agent framework & tools
│   │       │   ├── llm/           # LLM clients (Ollama, OpenAI)
│   │       │   ├── rag/           # RAG engine & vector store
│   │       │   ├── config.py      # Configuration
│   │       │   └── agent_factory.py
│   │       ├── routes/            # API endpoints
│   │       │   └── agent_routes.py # 🆕 Agent API
│   │       ├── models/            # Database models
│   │       ├── speech/            # Whisper integration
│   │       └── app.py             # Flask application
│   │
│   └── frontend/
│       └── src/
│           ├── components/        # React components
│           ├── pages/             # Page components
│           └── services/          # API clients
│
├── docs/                          # 🆕 Documentation
│   └── SETUP.md                   # Setup guide
├── scripts/                       # 🆕 Utility scripts
│   ├── setup.ps1                  # Quick setup
│   └── start-all.ps1              # Start all services
└── docker-compose.yml             # Docker setup
```

## 🛠️ Tech Stack

### Backend
- **Python 3.9+** - Core language
- **Flask** - Web framework
- **Ollama** - Local LLM inference
- **LangChain** - LLM orchestration
- **ChromaDB** - Vector database
- **Sentence Transformers** - Embeddings
- **OpenAI Whisper** - Speech-to-text
- **SQLAlchemy** - Database ORM
- **Flask-SocketIO** - WebSocket support

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **shadcn/ui** - UI components

### Infrastructure
- **Docker & Docker Compose** - Containerization
- **PostgreSQL** - Relational database
- **MongoDB** - Document database

## 🚀 Quick Start

### Prerequisites
1. **Install Ollama**: Download from [ollama.ai](https://ollama.ai)
2. **Pull a model**: `ollama pull llama3.2`
3. **Python 3.9+** and **Node.js 18+**

### Option 1: Automated Setup (Windows)

```powershell
# Run the setup script
.\scripts\setup.ps1

# Start all services
.\scripts\start-all.ps1
```

### Option 2: Manual Setup

**1. Install Dependencies**
```bash
# Backend
cd packages/backend/server
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Frontend
cd ../../frontend
npm install
```

**2. Configure Environment**
```bash
# Create .env in packages/backend/server/
LLM_MODEL=llama3.2
OLLAMA_HOST=http://localhost:11434
```

**3. Start Services**
```bash
# Terminal 1 - Backend
cd packages/backend/server
python app.py

# Terminal 2 - Frontend
cd packages/frontend
npm run dev
```

**4. Open Browser**
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:5000`

📖 **Detailed Setup**: See [docs/SETUP.md](docs/SETUP.md)

## 💡 Usage Examples

### Basic Chat
```bash
curl -X POST http://localhost:5000/api/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello, who are you?"}'
```

### Using Tools
```bash
# Calculator
curl -X POST http://localhost:5000/api/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is 156 * 23?"}'

# Web Search
curl -X POST http://localhost:5000/api/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Search for the latest AI news"}'
```

### Check Agent Stats
```bash
curl http://localhost:5000/api/agent/stats
```

## 🔧 Configuration

Environment variables in `.env`:

```env
# LLM Configuration
LLM_MODEL=llama3.2              # Model to use
OLLAMA_HOST=http://localhost:11434
LLM_TEMPERATURE=0.7             # Creativity (0-1)
LLM_MAX_TOKENS=2000             # Max response length

# RAG Configuration
RAG_MAX_DOCS=5                  # Context documents to retrieve
RAG_SIMILARITY=0.7              # Similarity threshold
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Agent Configuration
AGENT_MAX_ITERATIONS=5          # Max reasoning steps
AGENT_ENABLE_TOOLS=true         # Enable tool execution
AGENT_ENABLE_MEMORY=true        # Enable learning
```

## 📚 API Reference

### Agent Endpoints

**POST** `/api/agent/query`
- Process a query through the agent
- Body: `{"query": "your question", "conversation_history": [...]}`

**GET** `/api/agent/stats`
- Get agent statistics and configuration

**GET** `/api/agent/tools`
- List available tools

### Legacy Endpoints
- `/api/chat/*` - Chat management
- `/api/auth/*` - Authentication
- `/api/speech/*` - Speech processing

## 🎨 Customization

### Adding Custom Tools

Create a new tool in `core/agent/tools.py`:

```python
class MyCustomTool(Tool):
    def __init__(self):
        super().__init__(
            name="my_tool",
            description="What my tool does",
            parameters=[
                ToolParameter(name="input", type="string", description="Input data")
            ]
        )
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        # Your tool logic here
        return {'success': True, 'result': 'output'}
```

Register it in `core/agent_factory.py`:
```python
tool_registry.register(MyCustomTool())
```

### Switching Models

```bash
# Pull a different model
ollama pull mistral

# Update .env
LLM_MODEL=mistral

# Restart backend
```

## 🐛 Troubleshooting

**Ollama not connecting?**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve
```

**ChromaDB errors?**
```bash
# Clear vector store
rm -rf packages/backend/server/data/vector_store
```

**Port conflicts?**
- Backend: Change `PORT` in `.env`
- Frontend: Change port in `vite.config.ts`

## 🤝 Contributing

This is a portfolio project, but suggestions are welcome! Feel free to:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📝 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- **Ollama** - Local LLM inference
- **LangChain** - LLM framework
- **ChromaDB** - Vector database
- **OpenAI** - Whisper model
- **Hugging Face** - Transformers and embeddings
