# Email Agent

AI-powered email automation agent with LangGraph-based workflows for intelligent email processing.

## Quick Start

```bash
# Install dependencies (first time)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# Restart terminal, then:
uv sync

# Configure environment
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# Run backend and agent (in separate terminals)
.venv/Scripts/python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 5001 --reload
.venv/Scripts/python.exe -m uvicorn agent.main:app --host 0.0.0.0 --port 8000 --reload

# Run frontend (in a third terminal)
cd frontend
npm install   # first time only
npm run dev
```

## Demos
### Basic features
[Link to demo](https://drive.google.com/file/d/1q67BI7Kdj75FA0ieiw4fzmsJ9Tl-Lx2I/view?usp=sharing)

## Services

| Service  | URL                      | Description              |
| -------- | ------------------------ | ------------------------ |
| Frontend | http://localhost:5173    | React UI (Vite)          |
| Backend  | http://localhost:5001    | Auth, email, proxy API   |
| Agent    | http://localhost:8000    | LangGraph agent API      |

## Test Users

| Username | Password    |
| -------- | ----------- |
| alice    | password123 |
| bob      | password123 |
| charlie  | password123 |

## Features

- **Inbox / Sent / Deleted** tabs with real-time refresh
- **Compose** with To, CC, BCC fields
- **Email summarization** via AI (Summarize button in email reader)
- **AI Assistant** chat widget with multi-thread support
- **Draft with AI** — agent drafts emails from natural language prompts
- **Calendar** view for scheduled meetings
- **WebSocket** push notifications for new emails and agent events

## Tech Stack

- **Python** 3.11+ / **FastAPI** — backend & agent APIs
- **LangGraph** — agent workflow orchestration
- **Google Gemini** — LLM
- **SQLite** — database
- **React** + **TypeScript** + **Vite** — frontend
- **Zustand** + **TanStack Query** — state management
- **Tailwind CSS** — styling
- **WebSocket** — real-time notifications

## Project Structure

```
email-agent/
├── agent/                  # Agent API (port 8000)
├── backend/                # Backend API (port 5001)
│   ├── routes/             # Auth, email, calendar routes
│   ├── services/           # Mail, calendar services
│   └── static/             # Legacy static UI
├── config/                 # Prompts and settings
├── frontend/               # React frontend (port 5173)
│   └── src/
│       ├── api/            # API client and types
│       ├── components/     # UI components
│       ├── hooks/          # WebSocket hook
│       └── store/          # Zustand store
├── src/                    # Core agent library
│   ├── agent/              # Graph, nodes, tools, RAG
│   └── integrations/       # Mail and calendar clients
└── email-agent.db          # SQLite database
```

## Testing

```bash
# Install test dependencies
uv sync --group test

# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov=agent --cov-report=term-missing

# Run specific categories
pytest tests/unit/
pytest tests/integration/
pytest -k "test_login"
pytest -v
```

### Test Files

| File | Description |
| ---- | ----------- |
| `tests/unit/test_exceptions.py` | Exception handling |
| `tests/unit/test_mail_service.py` | Mail service logic |
| `tests/unit/test_llm_client.py` | LLM client |
| `tests/integration/test_auth_routes.py` | Auth endpoints |
| `tests/integration/test_email_routes.py` | Email CRUD |
| `tests/integration/test_user_routes.py` | User management |
| `tests/integration/test_agent_routes.py` | Agent workflow |
| `tests/integration/test_agent_proxy.py` | Backend→agent proxy |
| `tests/integration/test_health.py` | Health checks |
| `tests/integration/test_backend_ws.py` | Backend WebSocket |
| `tests/integration/test_agent_ws.py` | Agent WebSocket |
