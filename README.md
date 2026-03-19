# Email Agent

AI-powered email automation agent with LangGraph-based workflows for intelligent email processing.

## Project Overview

The Email Agent is a multi-service system that:

- Routes incoming emails to appropriate workflows
- Handles meeting scheduling with calendar integration
- Manages email drafts with human-in-the-loop approval
- Provides real-time WebSocket notifications

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Client    │────▶│   Agent API  │────▶│   Backend   │
│             │◀────│  (Port 8000) │◀────│ (Port 5001) │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    │  LangGraph  │
                    │  Workflows  │
                    └─────────────┘
```

## Actual Directory Structure

```
email-agent/
│
├── README.md
├── .env.example
├── .gitignore
├── .python-version
├── pyproject.toml
├── uv.lock
├── email-agent.db              # SQLite database
│
├── agent/                      # Agent API service (FastAPI)
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── dependencies.py
│   ├── routes/
│   │   ├── __init__.py
│   │   └── agent.py            # Agent endpoints (/draft, /thread, /process, /chat)
│   └── services/
│       ├── __init__.py
│       ├── agent_service.py    # Core agent logic (788 lines)
│       └── ws_client.py        # WebSocket client to backend
│
├── backend/                    # Email backend service (FastAPI)
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── database.py             # SQLAlchemy setup + seed data
│   ├── models.py               # User, Email models
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py             # /api/auth/signup, /api/auth/login
│   │   ├── email.py            # Email CRUD endpoints
│   │   └── ws_notifications.py # WebSocket push notifications
│   └── services/
│       ├── __init__.py
│       └── mail_service.py     # Email business logic
│
├── config/
│   ├── __init__.py
│   └── settings.py             # Pydantic settings
│
├── src/                        # Core library
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── states.py           # AgentState, MeetingData, EmailData
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   └── client.py       # Google Gemini LLM client
│   │   └── mail/
│   │       ├── __init__.py
│   │       ├── client.py       # Async HTTP client to backend
│   │       └── sync_client.py  # Sync mail operations
│   ├── memory/
│   │   ├── __init__.py
│   │   └── checkpointer.py     # LangGraph MemorySaver
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── shared/
│   │   │   ├── __init__.py
│   │   │   ├── decision_nodes.py # classify_workflow
│   │   │   └── email_nodes.py    # draft, approve, send, wait, followup
│   │   └── specialized/
│   │       ├── __init__.py
│   │       └── meeting_nodes.py # Meeting scheduling nodes
│   └── workflows/
│       ├── __init__.py
│       ├── router.py           # Main LangGraph router
│       └── meeting_scheduler.py # Meeting scheduling workflow
│
├── scripts/
│   ├── __init__.py
│   └── run.py                  # CLI test script
│
├── test/
│   └── __init__.py
│
└── notebook/                   # For Jupyter notebooks
```

## Installation

### Prerequisites

- Python 3.10 or higher
- uv (recommended) or pip

### Steps

1. **Clone the repository**

    ```bash
    git clone <repository-url>
    cd email-agent
    ```

2. **Create virtual environment**

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # Linux/macOS
    # .venv\Scripts\activate   # Windows
    ```

3. **Install dependencies**

    ```bash
    # Using uv (recommended)
    uv sync

    # Or using pip
    pip install -e .
    ```

4. **Configure environment variables**

    ```bash
    cp .env.example .env
    ```

    Edit `.env` and set your configuration:

    ```env
    # Database
    DATABASE_URL=sqlite:///email-agent.db

    # Email Backend
    EMAIL_BACKEND_HOST=0.0.0.0
    EMAIL_BACKEND_PORT=5001
    WS_BACKEND_URL=ws://localhost:5001

    # Agent API
    AGENT_HOST=0.0.0.0
    AGENT_PORT=8000

    # External Services
    GOOGLE_API_KEY=your_google_api_key_here
    ```

## Running the Application

### Start Backend API (Port 5001)

The backend handles email storage, user authentication, and WebSocket notifications.

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 5001 --reload
```

### Start Agent API (Port 8000)

The agent handles email processing, workflow routing, and LLM interactions.

```bash
uvicorn agent.main:app --host 0.0.0.0 --port 8000 --reload
```

### Run CLI Test Script

Test the meeting scheduler workflow:

```bash
python scripts/run.py
```

## Workflows

### Meeting Scheduler

Handles meeting requests by:

1. Extracting meeting details (date, time, participants)
2. Checking for missing information
3. Drafting confirmation email
4. Sending for human approval
5. Sending confirmation or follow-up

### Email Auto-Responder

Routes and responds to emails based on intent classification.

## API Endpoints

### Agent API (Port 8000)

| Method | Endpoint                        | Description                           |
| ------ | ------------------------------- | ------------------------------------- |
| POST   | `/api/agent/draft`              | Create/read/update/send/cancel drafts |
| GET    | `/api/agent/thread/{thread_id}` | Get thread messages                   |
| POST   | `/api/agent/process`            | Process an email with the agent       |
| POST   | `/api/agent/chat`               | Chat with the agent                   |
| WS     | `/api/agent/ws/{user_id}`       | WebSocket for real-time updates       |
| GET    | `/health`                       | Health check                          |

### Backend API (Port 5001)

| Method | Endpoint                 | Description                  |
| ------ | ------------------------ | ---------------------------- |
| POST   | `/api/auth/signup`       | User registration            |
| POST   | `/api/auth/login`        | User login                   |
| POST   | `/api/emails/send`       | Send email                   |
| POST   | `/api/emails/reply`      | Reply to email               |
| GET    | `/api/emails/inbox`      | Get inbox                    |
| GET    | `/api/emails/sent`       | Get sent emails              |
| GET    | `/api/emails/{email_id}` | Get specific email           |
| GET    | `/api/emails/query`      | Query emails                 |
| GET    | `/api/emails/poll`       | Poll for new emails          |
| WS     | `/ws/push/{user_id}`     | WebSocket push notifications |
| GET    | `/health`                | Health check                 |

## Test Users

The database is seeded with test users:

| Username | Password    |
| -------- | ----------- |
| alice    | password123 |
| bob      | password123 |
| charlie  | password123 |
