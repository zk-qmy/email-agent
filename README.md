# Email Agent

AI-powered email automation agent with LangGraph-based workflows for intelligent email processing.

## Quick Start

```bash
# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# Run both services (in separate terminals)
uvicorn backend.main:app --host 0.0.0.0 --port 5001 --reload
uvicorn agent.main:app --host 0.0.0.0 --port 8000 --reload
```

## Testing with Web UI

1. Open `http://localhost:5001/` in browser
2. Select a user from dropdown (alice/bob/charlie)
3. Go to **Agent** tab

**Workflow:**
```
1. Create Thread → enter prompt → copy thread_id from response
2. Get Thread → paste thread_id to check status
3. Reply Thread → paste thread_id → enter "y" to approve (or feedback to revise)
4. Repeat steps 2-3 until draft is ready
5. Draft is sent automatically when approved
```

## Test Users

| Username | Password    |
| -------- | ----------- |
| alice    | password123 |
| bob      | password123 |
| charlie  | password123 |

## Testing

Install test dependencies:

```bash
uv sync --group test
```

Run all tests:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=backend --cov=agent --cov-report=term-missing
```

Run specific categories:

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Specific test file
pytest tests/integration/test_auth_routes.py

# Tests matching pattern
pytest -k "test_login"
```

Run with verbose output:

```bash
pytest -v
```

### Test Categories

| Category | Description |
| -------- | ----------- |
| `tests/unit/` | Unit tests for exceptions, mail service, LLM client |
| `tests/integration/` | Integration tests for all API routes and WebSocket |

### Test Files

- `tests/unit/test_exceptions.py` - Exception handling tests
- `tests/unit/test_mail_service.py` - Mail service business logic tests
- `tests/unit/test_llm_client.py` - LLM client tests
- `tests/integration/test_auth_routes.py` - Authentication endpoints
- `tests/integration/test_email_routes.py` - Email CRUD endpoints
- `tests/integration/test_user_routes.py` - User management endpoints
- `tests/integration/test_agent_routes.py` - Agent workflow endpoints
- `tests/integration/test_agent_proxy.py` - Backend to agent proxy
- `tests/integration/test_health.py` - Health check endpoints
- `tests/integration/test_backend_ws.py` - Backend WebSocket tests
- `tests/integration/test_agent_ws.py` - Agent WebSocket tests

## Tech Stack

- **Python** 3.11+
- **FastAPI** - API services
- **LangGraph** - Workflow orchestration
- **Google Gemini** - LLM
- **SQLite** - Database
- **WebSocket** - Real-time notifications

## Project Structure

```
email-agent/
├── agent/            # Agent API (port 8000)
├── backend/          # Backend API (port 5001) + static UI
├── config/           # Settings + prompts
├── src/              # Core library
│   ├── agent/        # Graph, nodes, tools
│   └── integrations/# LLM + mail clients
└── email-agent.db   # SQLite database
```
