Master Orchestrator Mode (Active): 你现在的身份是“首席架构监工”。你的职责是根据 PROGRESS.md 里的任务进行自主决策。 决策链逻辑：

读取 PROGRESS.md 确定当前任务。

自动切换至最合适的 Agent（如 /agent-switch architect）。

执行对应的 /skill。

获取反馈后（报错或成功），更新 PROGRESS.md 的状态。

自动开启下一个任务，无需询问我。
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BrightChat is a full-stack AI chat application workbench with real-time LLM integration, user management, model administration, knowledge base (RAG), and Agent capabilities. It supports multiple users, configurable LLM models, streaming chat responses, document-based knowledge retrieval, and LangGraph-powered agents.

**Tech Stack:**
- Frontend: React 19 + TypeScript + Vite 6
- Backend: Python 3.11 + FastAPI + SQLAlchemy
- Database: MySQL (port 13306)
- Vector Database: ChromaDB (port 8002 internal)
- Deployment: Docker Compose with Nginx reverse proxy
- Agent Framework: LangGraph
- Embedding Model: BGE-large-zh-v1.5 (Sentence Transformers)

---

## Development Commands

### Local Development

```bash
# Backend (FastAPI on port 18080)
cd backend-python
source venv/bin/activate
python minimal_api.py

# Frontend (Vite dev server on port 3000)
cd frontend
npm run dev
npm run build          # Production build

# ChromaDB (vector database for RAG)
docker run -d -p 8002:8000 --name bright-chat-chromadb chromadb/chroma:latest

# Mock Server (optional, on port 8080)
cd mockserver
python start.py
```

### Docker Deployment

```bash
# One-click deployment
./deploy.sh            # Build and start all services
./stop-deploy.sh       # Stop services

# Manual Docker commands
docker compose up -d
docker compose logs -f --tail=100
docker compose ps
```

### Database Operations

```bash
# Access MySQL in Docker
docker exec -it AIWorkbench-mysql mysql -u bright_chat -p

# Direct database connection (if exposed)
mysql -h 47.116.218.206 -P 13306 -u root -p

# Run migrations
cd backend-python
python execute_migration.py  # Run migration files
```

---

## Architecture Overview

### Dual Backend Implementation

The codebase contains **two backend implementations**:

1. **`minimal_api.py`** (2100+ lines) - Single-file implementation, **currently active**
2. **`app/` directory** - Modular structure with separate files for routes, models, services

**Important:** When making backend changes, update `minimal_api.py` as it is the running implementation.

### Backend Module Structure

```
backend-python/app/
├── agents/           # Agent module (LangGraph-based)
│   ├── agent_service.py    # Core agent workflow engine
│   ├── router.py           # Agent API endpoints
│   └── tools/              # Agent tool implementations
├── rag/              # RAG (Retrieval-Augmented Generation)
│   ├── config.py           # ChromaDB + BGE model configuration
│   ├── document_processor.py # Document parsing & chunking
│   ├── retriever.py        # Vector search utilities
│   └── router.py           # Knowledge base API endpoints
├── models/           # SQLAlchemy data models
│   ├── user.py             # User model
│   ├── session.py          # Chat session model
│   ├── agent.py            # Agent & AgentExecution models
│   ├── knowledge_base.py   # KnowledgeGroup, KnowledgeBase, Document
│   └── llm_model.py        # LLM model configuration
└── core/             # Core utilities
    ├── config.py           # Application settings
    └── database.py         # Database connection management
```

### Frontend Service Layer Pattern

Frontend uses service objects in `services/` directory for all API calls:
- `authService` - Login/logout
- `chatService` - LLM chat operations (streaming SSE)
- `sessionService` - Session & message management
- `modelService` - LLM model configuration (admin only)
- `favoriteService` - Message bookmarking
- `agentService` - Agent CRUD & chat (NEW)
- `knowledgeService` - Knowledge base & document management (NEW)
- `providerService` - LLM provider management
- `adminService` - Admin panel operations
- `gatewayServer` - Gateway API client
- `config` - Frontend configuration

**Mock Mode:** Set `USE_MOCK: true` in `frontend/config/index.ts` for offline development.

### Key Architecture Patterns

1. **Time Format Duality**:
   - Backend: ISO datetime strings (`2026-01-21T03:12:32`)
   - Frontend: Unix timestamps in milliseconds
   - Conversion happens in service layer

2. **View State Management** (`App.tsx`):
   - `view` state controls whether user sees chat or admin panel
   - **Always reset `view` to `'chat'` on login/logout** to prevent permission issues
   - Bug: admin users in admin view can leak view state to next logged-in user

3. **Streaming Responses**: LLM chat uses Server-Sent Events (SSE) for real-time streaming

4. **Agent Chat Flow**:
   - Agent uses LangGraph state machine (Think -> Act -> Observe loop)
   - Supports tools: calculator, datetime, knowledge_search, code_executor, browser, file
   - Session can be linked to an Agent via `agent_id` field
   - Frontend detects Agent session and switches to agent chat mode

5. **Role-Based Access Control**:
   - `admin` role: Full access including user management, model configuration, agent management
   - `user` role: Chat, favorites, knowledge bases, agents
   - Protected endpoints use `require_admin()` dependency

---

## Data Models

### Core Models

**Users**: id, username, password_hash (bcrypt + SHA256 fallback), role, created_at
**Sessions**: id, title, user_id, agent_id (nullable), last_updated, created_at
**Messages**: id, session_id, role (user/assistant/system), content, timestamp
**MessageFavorites**: Links users to favorited messages with optional notes

### LLM Models

**LLMModels**: id, name, display_name, model_type (openai/anthropic/custom/ias), api_url, api_key (plaintext), is_active, temperature, stream_supported

**Note:** API keys are stored in **plaintext** and visible to admin users by design.

### Agent Models

**Agent**: id, name, display_name, description, agent_type (rag/tool/custom), system_prompt, knowledge_base_ids (JSON), tools (JSON), config (JSON), is_active, created_by, created_at, updated_at

**AgentExecution**: id, agent_id, user_id, session_id, input_prompt, status (running/completed/failed), steps, result, error_message, execution_log (JSON), started_at, completed_at

**Agent Types**:
- `rag` - Knowledge base search agent
- `tool` - Tool-using agent (calculator, code executor, browser, etc.)
- `custom` - Custom configured agent

**Agent Tools** (predefined):
- `calculator` - Mathematical calculations
- `datetime` - Current date/time
- `knowledge_search` - Vector search in knowledge bases
- `code_executor` - Safe Python code execution
- `browser` - Web browsing, search, scraping
- `file` - File operations (read/write/list)

### Knowledge Base Models

**KnowledgeGroup**: id, name, description, user_id, color, created_at

**KnowledgeBase**: id, name, description, user_id, group_id, embedding_model (default: bge-large-zh-v1.5), chunk_size (default: 500), chunk_overlap (default: 50), is_active, created_at, updated_at

**Document**: id, knowledge_base_id, filename, file_type, file_size, chunk_count, upload_status (processing/completed/failed), error_message, uploaded_at, processed_at

**Vector Storage** (ChromaDB):
- Collection: `knowledge_chunks`
- Metadata per chunk: document_id, knowledge_base_id, user_id, chunk_index, filename, file_type

---

## Configuration

### Frontend Configuration (`frontend/config/index.ts`)

```typescript
{
  USE_MOCK: false,              // Toggle mock mode
  API_BASE_URL: '/api/v1',     // Dynamic: proxied in dev, relative in prod
  IAS_URL: '/lmp-cloud-ias-server/api/llm/chat/completions/V2',
  DEFAULT_MODEL: 'glm-4-flash'  // Configured model
}
```

**API Base URL Resolution**:
- Development: Uses Vite proxy (`/api/v1` -> `http://localhost:18080/api/v1`)
- Production: Uses relative path (routed through Nginx)
- Environment override: `VITE_API_BASE_URL`

### Backend Configuration (`backend-python/app/core/config.py`)

```python
# Server
SERVER_HOST: str = "0.0.0.0"
SERVER_PORT: int = 8080
API_PREFIX: str = "/api/v1"

# Database
DB_HOST: str = "47.116.218.206"
DB_PORT: int = 13306
DB_DATABASE: str = "bright_chat"

# JWT
JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-this-in-production"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

# ChromaDB (RAG)
CHROMADB_HOST: str = "localhost"
CHROMADB_PORT: int = 8000

# BGE Embedding Model
BGE_MODEL_PATH: str = "/data1/allresearchProject/Bright-Chat/models/Xorbits/bge-large-zh-v1.5"
RAG_USE_CHROMADB_EMBEDDING: bool = False
```

### Docker Environment (`.env` / `docker-compose.yml`)

Critical variables to modify in production:
- `MYSQL_ROOT_PASSWORD` - Database root password
- `MYSQL_PASSWORD` - Application database password
- `JWT_SECRET_KEY` - JWT signing key (min 32 characters)
- `SERVER_WORKERS` - Backend worker count (default: 4)

**Service Ports** (Docker internal vs external):
- Backend: `18080:18080`
- Frontend: `3000:80`
- MySQL: `13306:3306`
- Redis: `6379:6379`
- ChromaDB: `8002:8000`
- Nginx: `80:80`, `443:443`

---

## API Endpoint Structure

### Authentication Endpoints

| Endpoint | Method | Access | Description |
|----------|--------|--------|-------------|
| `/api/v1/auth/login` | POST | Public | User authentication |
| `/api/v1/auth/logout` | POST | Authenticated | Session termination |

### User Management (Admin)

| Endpoint | Method | Access | Description |
|----------|--------|--------|-------------|
| `/api/v1/admin/users` | GET | Admin | List all users |
| `/api/v1/admin/users` | POST | Admin | Create user |
| `/api/v1/admin/users/{user_id}` | GET | Admin | Get user details |
| `/api/v1/admin/users/{user_id}` | PUT | Admin | Update user |
| `/api/v1/admin/users/{user_id}` | DELETE | Admin | Delete user |

### Session & Message Endpoints

| Endpoint | Method | Access | Description |
|----------|--------|--------|-------------|
| `/api/v1/sessions` | GET | Authenticated | Get user sessions |
| `/api/v1/sessions` | POST | Authenticated | Create session (with agent_id) |
| `/api/v1/sessions/{session_id}/messages` | GET | Authenticated | Get session messages |
| `/api/v1/sessions/{session_id}/messages` | POST | Authenticated | Save messages |
| `/api/v1/sessions/{session_id}` | DELETE | Authenticated | Delete session |

### LLM Model Endpoints

| Endpoint | Method | Access | Description |
|----------|--------|--------|-------------|
| `/api/v1/models/active` | GET | Authenticated | Get active models (no API keys) |
| `/api/v1/admin/models` | GET | Admin | List all models (with API keys) |
| `/api/v1/admin/models` | POST | Admin | Create model |
| `/api/v1/admin/models/{model_id}` | GET | Admin | Get model details |
| `/api/v1/admin/models/{model_id}` | PUT | Admin | Update model |
| `/api/v1/admin/models/{model_id}` | DELETE | Admin | Delete model |
| `/api/v1/lmp-cloud-ias-server/...` | POST | Authenticated | LLM chat proxy (streaming) |

### Agent Endpoints (NEW)

| Endpoint | Method | Access | Description |
|----------|--------|--------|-------------|
| `/api/v1/agents/` | GET | Authenticated | List all agents |
| `/api/v1/agents/` | POST | Admin | Create agent |
| `/api/v1/agents/{agent_id}` | GET | Authenticated | Get agent details |
| `/api/v1/agents/{agent_id}` | PUT | Admin | Update agent |
| `/api/v1/agents/{agent_id}` | DELETE | Admin | Delete agent |
| `/api/v1/agents/{agent_id}/chat` | POST | Authenticated | Agent chat (SSE streaming) |
| `/api/v1/agents/{agent_id}/executions/` | GET | Authenticated | Get execution history |
| `/api/v1/agents/tools/` | GET | Authenticated | List available tools |
| `/api/v1/agents/service-health/` | GET | Public | Agent service health check |

**Agent Chat Request Format**:
```json
{
  "query": "用户消息或问题",
  "session_id": "optional-session-id",
  "stream": true
}
```

**Agent Chat SSE Events**:
- `{"type": "start", "execution_id": "...", "agent_name": "...", "query": "..."}`
- `{"type": "step", "node": "think/act/observe", "step": 1, "state": {...}}`
- `{"type": "tool_call", "tool": "calculator", "parameters": {...}, "result": "..."}`
- `{"type": "complete", "output": "...", "steps": 3, "duration": 1.5}`
- `{"type": "error", "error": "..."}`

### Knowledge Base Endpoints (NEW)

| Endpoint | Method | Access | Description |
|----------|--------|--------|-------------|
| `/api/v1/knowledge/groups` | GET | Authenticated | List user's groups |
| `/api/v1/knowledge/groups` | POST | Authenticated | Create group |
| `/api/v1/knowledge/groups/{group_id}` | DELETE | Authenticated | Delete group |
| `/api/v1/knowledge/bases` | GET | Authenticated | List knowledge bases |
| `/api/v1/knowledge/bases` | POST | Authenticated | Create knowledge base |
| `/api/v1/knowledge/bases/{kb_id}` | GET | Authenticated | Get KB details |
| `/api/v1/knowledge/bases/{kb_id}` | DELETE | Authenticated | Delete KB |
| `/api/v1/knowledge/bases/{kb_id}/documents` | GET | Authenticated | List documents |
| `/api/v1/knowledge/bases/{kb_id}/documents` | POST | Authenticated | Upload document |
| `/api/v1/knowledge/bases/{kb_id}/documents/{doc_id}` | GET | Authenticated | Get document |
| `/api/v1/knowledge/bases/{kb_id}/documents/{doc_id}` | DELETE | Authenticated | Delete document |
| `/api/v1/knowledge/bases/{kb_id}/documents/{doc_id}/chunks` | GET | Authenticated | Get document chunks |
| `/api/v1/knowledge/search` | GET | Authenticated | Semantic search |

**Document Upload Parameters**:
- `file`: Document file (PDF, DOCX, TXT, MD, HTML, XLS, XLSX, PPT, PPTX)
- `sync`: true for immediate processing, false for background (default)
- `chunk_size`: Text chunk size (default: 500)
- `chunk_overlap`: Chunk overlap (default: 50)

**Search Parameters**:
- `query`: Search query text
- `knowledge_base_ids`: Comma-separated KB IDs (optional, searches all if omitted)
- `top_k`: Number of results (default: 5)

### Favorite Endpoints

| Endpoint | Method | Access | Description |
|----------|--------|--------|-------------|
| `/api/v1/messages/{message_id}/favorite` | POST | Authenticated | Add favorite |
| `/api/v1/messages/{message_id}/favorite` | DELETE | Authenticated | Remove favorite |
| `/api/v1/favorites` | GET | Authenticated | List favorites |
| `/api/v1/messages/{message_id}/favorite-status` | GET | Authenticated | Check status |

### System Endpoints

| Endpoint | Method | Access | Description |
|----------|--------|--------|-------------|
| `/health` | GET | Public | Basic health check |
| `/api/v1/system/health` | GET | Authenticated | Detailed health (DB, ChromaDB, BGE) |

API docs available at: `http://localhost:18080/docs`

---

## Docker Services Architecture

```
                                    ┌─────────────────────────────────────────┐
                                    │         Nginx (ports 80, 443)          │  Reverse proxy
                                    └──────────────┬──────────────────────────┘
                                                   │
                                           ┌───────┴────────┐
                                           ▼                ▼
                                    ┌──────────┐      ┌──────────┐
                                    │ Frontend │      │ Backend  │
                                    │ :8080    │      │ :18080   │
                                    └──────────┘      └─────┬────┘
                                                             │
                                      ┌────────────────────────┴────────┐
                                      ▼                                 ▼
                                ┌─────────────┐                  ┌─────────────┐
                                │   MySQL     │                  │   Redis     │
                                │   :13306    │                  │   :6379     │
                                └─────────────┘                  └─────────────┘
                                      │
                                      ▼
                                ┌─────────────┐
                                │  ChromaDB   │  Vector DB for RAG
                                │   :8002     │
                                └─────────────┘
```

### Service Dependencies

- **Backend** depends on: MySQL, Redis, ChromaDB
- **Frontend** depends on: Backend
- **Nginx** depends on: Frontend, Backend

### Port Mapping

| Port | Service | Exposed | Purpose |
|------|---------|---------|---------|
| 80 | Nginx | Yes | Main HTTP entry |
| 443 | Nginx HTTPS | Optional | Main HTTPS entry |
| 3000 | Frontend | No | Vite dev server (local only) |
| 8080 | Frontend | No | Production frontend (internal) |
| 18080 | Backend | No | FastAPI backend (internal) |
| 13306 | MySQL | Optional | MySQL database |
| 6379 | Redis | Optional | Cache/queue |
| 8002 | ChromaDB | No | Vector database (internal) |

---

## Important Conventions

1. **Password Hashing**: Bcrypt with SHA256 fallback for legacy compatibility
2. **Temperature Storage**: Stored as integer (70 = 0.70) in database
3. **Chinese Comments**: Many code comments are in Chinese
4. **Default Credentials**: `admin` / `pwd123`
5. **Timezone**: Asia/Shanghai (configured in Docker)
6. **Backend Port**: 18080 (non-standard to avoid conflicts)
7. **Session-Agent Link**: Sessions can have an `agent_id` to indicate Agent conversations
8. **Document Processing**: Supports sync/async modes with retry mechanism (3 attempts)

---

## Common Issues

### Database Migration After Schema Changes

If you modify database models, run migration scripts:

```bash
cd backend-python
python execute_migration.py  # Auto-detects and runs migrations
```

Or manually apply SQL:
```sql
-- Example: Add agent_id to sessions
ALTER TABLE sessions ADD COLUMN agent_id VARCHAR(36) NULL;
CREATE INDEX ix_sessions_agent_id ON sessions(agent_id);
```

### View State Bug Prevention

When modifying `App.tsx` login/logout logic, ensure `view` state is reset:

```typescript
const onLogin = (user: User) => {
  setCurrentUser(user);
  setView('chat');  // Always reset to chat on login
};

const handleLogout = async () => {
  // ... cleanup
  setView('chat');  // Always reset to chat on logout
};
```

### Agent Session State Management

When switching sessions:
1. Check if session has `agentId`
2. Load agent details from backend
3. Set `selectedAgent` state
4. Clear `selectedAgent` for new chats

```typescript
const onSelectSession = async (id: string) => {
  const session = sessions.find(s => s.id === id);
  if (session?.agentId) {
    const agentApi = await agentService.getAgent(session.agentId);
    setSelectedAgent(convertToAgent(agentApi));
  } else {
    setSelectedAgent(null); // Regular chat
  }
};
```

### ChromaDB Connection Issues

If ChromaDB connection fails:
```bash
# Check ChromaDB container
docker ps | grep chromadb

# Restart ChromaDB
docker restart AIWorkbench-chromadb

# Manual ChromaDB for testing
docker run -d -p 8002:8000 chromadb/chroma:latest
```

### Document Upload Processing

Documents process in background with retry:
- Status: `pending` -> `processing` -> `completed` / `error`
- Use `sync=true` for immediate processing
- Max file size: 50MB (configurable)
- Supported formats: PDF, DOCX, TXT, MD, HTML, XLS, XLSX, PPT, PPTX

---

## Frontend Components

### Main Components

- `App.tsx` - Root application with state management
- `Login.tsx` - Authentication screen
- `Sidebar.tsx` - Navigation with sessions, agents, knowledge bases
- `TopBar.tsx` - Model/agent selector and user menu
- `ChatInput.tsx` - Message input with send button
- `AdminPanel.tsx` - Admin management interface
- `FavoriteModal.tsx` - Favorited messages viewer

### Sidebar Sections

- `SessionTrailSection.tsx` - Chat session list
- `AgentSection.tsx` - Agent list and selection
- `KnowledgeSection.tsx` - Knowledge base groups
- `KnowledgeModal.tsx` - Knowledge base management dialog

### Knowledge Components

- `KnowledgePanel.tsx` - Knowledge base viewer
- `KnowledgeSelector.tsx` - Multi-select for knowledge bases
- `KnowledgeBaseDetail.tsx` - Knowledge base with document list
- `DocumentChunksDetail.tsx` - Document chunk viewer

---

## Testing

Test files in `backend-python/`:
- `comprehensive_regression_test.py` - Full regression test suite
- `e2e_test.py` - End-to-end API tests
- `integration_test.py` - Service integration tests
- `test_message_order.py` - Message ordering tests
- `test_agent_*.py` - Agent-specific tests
- `test_rag_*.py` - RAG/knowledge base tests

Run with pytest (requires test environment setup):
```bash
cd backend-python
pytest -v
pytest tests/test_agent_chat.py -v  # Run specific test
```

---

## File Security Best Practices

1. **Path Traversal Protection**: Always validate file paths in document uploads
   ```python
   safe_path = (UPLOAD_DIR / filename).resolve()
   if not safe_path.is_relative_to(UPLOAD_DIR.resolve()):
       raise HTTPException(400, "Invalid file path")
   ```

2. **File Size Limits**: Enforce maximum upload size
   ```python
   MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
   ```

3. **File Type Validation**: Check MIME types and extensions
   ```python
   ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}
   ```

---

## Development Workflow

### Adding a New Feature

1. **Backend Changes**:
   - Add models to `backend-python/app/models/`
   - Add routes to `minimal_api.py` (or modular router)
   - Update `frontend/services/*.ts` for API calls

2. **Frontend Changes**:
   - Add types to `frontend/types.ts`
   - Add/modify components in `frontend/components/`
   - Update `App.tsx` for state management

3. **Testing**:
   - Write tests in `backend-python/tests/`
   - Test with `pytest -v`
   - Verify frontend with browser DevTools

### Agent Development

To add a new tool to Agent:
1. Implement tool function in `backend-python/app/agents/tools/`
2. Register in `AgentService._register_default_tools()`
3. Update `AgentService._decide_tool()` for tool selection logic
4. Add output formatting in `AgentService._format_tool_output()`

### Knowledge Base Development

To add new document type support:
1. Add loader to `DocumentProcessor.load_document()`
2. Update `SUPPORTED_FILE_TYPES` in `rag/config.py`
3. Test with `test_rag_endpoints.sh`

---

## Troubleshooting

### Backend Won't Start

```bash
# Check database connection
docker exec -it AIWorkbench-mysql mysql -u bright_chat -p -e "SELECT 1"

# Check ChromaDB
curl http://localhost:8002/api/v1/heartbeat

# Check backend logs
docker logs -f AIWorkbench-backend
```

### Agent Chat Not Working

```bash
# Check agent service health
curl http://localhost:18080/api/v1/agents/service-health/

# Verify agent exists
curl http://localhost:18080/api/v1/agents/

# Check LangGraph dependencies
pip list | grep langgraph
pip list | grep langchain
```

### Knowledge Base Search Returns No Results

```bash
# Check ChromaDB collection
curl http://localhost:8002/api/v1/collections

# Verify BGE model
ls -la /data1/allresearchProject/Bright-Chat/models/

# Test embedding
python -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('bge-large-zh-v1.5'); print(model.encode('test').shape)"
```
