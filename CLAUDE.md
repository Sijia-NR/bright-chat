# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BrightChat is a full-stack AI chat application workbench with real-time LLM integration, user management, and model administration. It supports multiple users, configurable LLM models, and streaming chat responses.

**Tech Stack:**
- Frontend: React 19 + TypeScript + Vite 6
- Backend: Python 3.11 + FastAPI + SQLAlchemy
- Database: MySQL (port 13306)
- Deployment: Docker Compose with Nginx reverse proxy

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
docker exec -it bright-chat-mysql mysql -u bright_chat -p

# Direct database connection (if exposed)
mysql -h 47.116.218.206 -P 13306 -u root -p

# Schema migration (if using Alembic)
cd backend-python
alembic upgrade head
```

---

## Architecture Overview

### Dual Backend Implementation

The codebase contains **two backend implementations**:

1. **`minimal_api.py`** (1100+ lines) - Single-file implementation, **currently active**
2. **`app/` directory** - Modular structure with separate files for routes, models, services

**Important:** When making backend changes, update `minimal_api.py` as it is the running implementation.

### Frontend Service Layer Pattern

Frontend uses service objects in `services/` directory for all API calls:
- `authService` - Login/logout
- `chatService` - Chat operations
- `sessionService` - Session management
- `modelService` - LLM model configuration (admin only)
- `favoriteService` - Message bookmarking

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

4. **Role-Based Access Control**:
   - `admin` role: Full access including user management and model configuration
   - `user` role: Chat and favorites only
   - Protected endpoints use `require_admin()` dependency

### Data Models

**Users**: id, username, password_hash (SHA256), role, created_at
**Sessions**: id, title, user_id, last_updated, created_at
**Messages**: id, session_id, role (user/assistant/system), content, timestamp
**MessageFavorites**: Links users to favorited messages with optional notes
**LLMModels**: id, name, display_name, model_type, api_url, api_key (plaintext), is_active, temperature, stream_supported

**Note:** API keys are stored in **plaintext** and visible to admin users by design.

---

## Configuration

### Frontend Configuration (`frontend/config/index.ts`)

```typescript
{
  USE_MOCK: false,              // Toggle mock mode
  API_BASE_URL: 'http://localhost:18080/api/v1',
  IAS_URL: '/lmp-cloud-ias-server/api/llm/chat/completions/V2',
  DEFAULT_MODEL: 'BrightChat-General-v1'
}
```

### Backend Configuration (`minimal_api.py`)

```python
DATABASE_URL = "mysql+pymysql://..."
SECRET_KEY = "your-super-secret-jwt-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours
API_PREFIX = "/api/v1"
```

### Docker Environment (`.env`)

Critical variables to modify in production:
- `MYSQL_ROOT_PASSWORD` - Database root password
- `MYSQL_PASSWORD` - Application database password
- `JWT_SECRET_KEY` - JWT signing key (min 32 characters)
- `SERVER_WORKERS` - Backend worker count (default: 4)

---

## API Endpoint Structure

| Endpoint | Method | Access | Description |
|----------|--------|--------|-------------|
| `/api/v1/auth/login` | POST | Public | User authentication |
| `/api/v1/auth/logout` | POST | Authenticated | Session termination |
| `/api/v1/admin/users` | GET/POST | Admin | User management |
| `/api/v1/sessions/` | GET/POST | Authenticated | Session CRUD |
| `/api/v1/sessions/{id}/messages` | GET/POST | Authenticated | Message operations |
| `/api/v1/favorites/*` | * | Authenticated | Message bookmarks |
| `/api/v1/admin/models` | GET/POST/PUT/DELETE | Admin | LLM model management |
| `/api/v1/models/active` | GET | Authenticated | Get active models |
| `/lmp-cloud-ias-server/...` | POST | Authenticated | LLM chat proxy (streaming) |

API docs available at: `http://localhost:18080/docs`

---

## Docker Services Architecture

```
┌─────────────────────────────────────────┐
│         Nginx (port 80)                 │  Reverse proxy + static files
└──────────────┬──────────────────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
┌──────────┐      ┌──────────┐
│ Frontend │      │ Backend  │
│ :8080    │      │ :18080   │
└──────────┘      └─────┬────┘
                       │
            ┌──────────┴────────┐
            ▼                   ▼
      ┌─────────┐         ┌─────────┐
      │ MySQL   │         │ Redis   │
      │ :13306  │         │ :6379   │
      └─────────┘         └─────────┘
```

### Port Mapping

| Port | Service | Exposed |
|------|---------|---------|
| 80 | Nginx | Yes (main entry) |
| 443 | Nginx HTTPS | Optional |
| 8080 | Frontend | No (internal) |
| 18080 | Backend | No (internal) |
| 13306 | MySQL | Optional |
| 6379 | Redis | Optional |

---

## Important Conventions

1. **Password Hashing**: Simple SHA256 (demo-grade, not production secure)
2. **Temperature Storage**: Stored as integer (70 = 0.70) in database
3. **Chinese Comments**: Many code comments are in Chinese
4. **Default Credentials**: `admin` / `pwd123`
5. **Timezone**: Asia/Shanghai (configured in Docker)
6. **Backend Port**: 18080 (non-standard to avoid conflicts)

---

## Common Issues

### Database Migration After Schema Changes

If you modify database models (e.g., `api_key_encrypted` → `api_key`), run:

```sql
ALTER TABLE llm_models CHANGE COLUMN api_key_encrypted api_key TEXT NOT NULL;
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

### Frontend Build Warnings

The warning about `/index.css` is expected - Vite handles it at runtime.

---

## Testing

Test files in `backend-python/`:
- `comprehensive_interface_test.py`
- `e2e_test.py`
- `integration_test.py`
- `test_message_order.py`

Run with pytest (requires test environment setup).
