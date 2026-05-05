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