# Eva AI Agent - Setup Guide

## Prerequisites

### Required Software
- **Python 3.9+** with pip
- **Node.js 18+** with npm/bun
- **Ollama** for local LLM (or LM Studio as alternative)
- **Git**
- **Docker & Docker Compose** (optional, for containerized deployment)

### System Requirements
- **RAM**: 8GB minimum (16GB recommended for larger models)
- **Storage**: 10GB+ free space (for models and data)
- **CPU**: Multi-core processor (GPU optional but recommended for Whisper)

---

## Step 1: Install Ollama

### Windows
1. Download Ollama from [ollama.ai](https://ollama.ai)
2. Run the installer
3. Verify installation:
```powershell
ollama --version
```

### Linux/Mac
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### Pull a Model
```bash
# Recommended: Llama 3.2 (3B parameters, fast and efficient)
ollama pull llama3.2

# Alternative: Mistral (7B parameters, more capable)
ollama pull mistral

# For coding tasks: CodeLlama
ollama pull codellama
```

### Verify Ollama is Running
```bash
ollama list
```

---

## Step 2: Clone and Setup Backend

### 1. Navigate to Backend Directory
```bash
cd packages/backend/server
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Download Spacy Model (for NLP)
```bash
python -m spacy download en_core_web_sm
```

### 5. Create Environment File
Create `.env` file in `packages/backend/server/`:

```env
# Flask Configuration
SECRET_KEY=your_secret_key_here_change_in_production
JWT_SECRET_KEY=your_jwt_secret_key_here_change_in_production
FLASK_ENV=development

# Database
DATABASE_URI=sqlite:///eva.db
# For PostgreSQL: postgresql://user:password@localhost:5432/eva

# LLM Configuration
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
OLLAMA_HOST=http://localhost:11434
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000

# RAG Configuration
RAG_COLLECTION=eva_memory
RAG_PERSIST_DIR=./data/vector_store
EMBEDDING_MODEL=all-MiniLM-L6-v2
RAG_MAX_DOCS=5
RAG_SIMILARITY=0.7

# Agent Configuration
AGENT_MAX_ITERATIONS=5
AGENT_ENABLE_TOOLS=true
AGENT_ENABLE_MEMORY=true
AGENT_ENABLE_LEARNING=true

# Whisper Configuration
WHISPER_MODEL=base
WHISPER_LANGUAGE=en
WHISPER_DEVICE=cpu

# Ports
PORT=5000
```

### 6. Initialize Database
```bash
python app.py
# Press Ctrl+C after it starts successfully
```

---

## Step 3: Setup Frontend

### 1. Navigate to Frontend Directory
```bash
cd ../../frontend
```

### 2. Install Dependencies
```bash
npm install
# or
bun install
```

### 3. Create Environment File
Create `.env` in `packages/frontend/`:

```env
VITE_API_URL=http://localhost:5000
VITE_WS_URL=ws://localhost:5000
VITE_NODE_API_URL=http://localhost:8081
```

---

## Step 4: Running the Application

### Option 1: Run Services Individually

**Terminal 1 - Python Backend:**
```bash
cd packages/backend/server
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd packages/frontend
npm run dev
# or
bun run dev
```

**Terminal 3 - Verify Ollama:**
```bash
ollama serve
```

### Option 2: Run with Docker Compose

```bash
# From project root
docker-compose up --build
```

---

## Step 5: Verify Installation

### 1. Check Backend
Open browser: `http://localhost:5000`

Expected response:
```json
{"message": "EVA Assistant API is running"}
```

### 2. Check Agent API
```bash
curl http://localhost:5000/api/agent/stats
```

Expected response:
```json
{
  "success": true,
  "stats": {
    "model": "llama3.2",
    "tools_available": 4,
    "memory_stats": {...}
  }
}
```

### 3. Check Frontend
Open browser: `http://localhost:5173`

You should see the Eva chat interface.

---

## Step 6: Test the Agent

### Test Query via API
```bash
curl -X POST http://localhost:5000/api/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is 25 * 4?"
  }'
```

Expected: Agent should use the calculator tool and return 100.

### Test Web Search
```bash
curl -X POST http://localhost:5000/api/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Search for the latest news about AI"
  }'
```

---

## Troubleshooting

### Ollama Connection Issues
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
# Windows: Restart from system tray
# Linux/Mac:
sudo systemctl restart ollama
```

### Python Dependencies Issues
```bash
# Upgrade pip
pip install --upgrade pip

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Port Already in Use
```bash
# Windows - Find and kill process
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:5000 | xargs kill -9
```

### ChromaDB/Vector Store Issues
```bash
# Clear vector store
rm -rf packages/backend/server/data/vector_store

# Restart the application
```

---

## Next Steps

1. **Configure Tools**: Edit `core/agent/tools.py` to add custom tools
2. **Customize System Prompt**: Modify `core/agent/agent.py`
3. **Add Knowledge**: Use the memory API to add domain knowledge
4. **Enable Whisper**: Uncomment audio handler in `app.py`
5. **Deploy**: Use Docker Compose for production deployment

---

## Useful Commands

### Check Logs
```bash
tail -f packages/backend/server/eva.log
```

### Reset Database
```bash
rm packages/backend/server/eva.db
python packages/backend/server/app.py
```

### Update Models
```bash
ollama pull llama3.2
```

### Run Tests
```bash
cd packages/backend/server
pytest tests/
```

---

## Performance Tips

1. **Use smaller models for development**: `llama3.2` (3B) is fast
2. **Use larger models for production**: `mistral` (7B) or `llama3.1` (8B)
3. **Enable GPU**: Set `WHISPER_DEVICE=cuda` if you have NVIDIA GPU
4. **Adjust context window**: Modify `RAG_MAX_DOCS` based on your needs
5. **Cache embeddings**: Vector store persists automatically

---

## Support

For issues and questions:
- Check logs in `eva.log`
- Review Ollama logs: `ollama logs`
- Verify all services are running on correct ports
