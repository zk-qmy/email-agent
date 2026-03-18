# Email Agent


## Tentative Directory Structure

```
email-agent/
│
├── README.md
├── .env.example
├── .gitignore
├── requirements.txt
├── pyproject.toml
├── Dockerfile
│
├── config/
│   ├── __init__.py
│   ├── settings.py                 # All configuration (Pydantic)
│   │
│   ├── prompts/                    # Prompt templates by workflow
│   │   ├── meeting_scheduler.yaml
│   │   ├── support_ticket.yaml
│   │   ├── auto_responder.yaml
│   │   └── shared.yaml             # Common prompts
│   │
│   └── templates/                  # Email response templates
│       ├── meeting_confirmation.jinja2
│       ├── support_ack.jinja2
│       └── generic_reply.jinja2
│
├── src/
│   ├── __init__.py
│   │
│   ├── core/                       # Core framework
│   │   ├── __init__.py
│   │   ├── state.py                # State schemas for all workflows
│   │   ├── exceptions.py           # Custom exceptions
│   │   └── types.py                # Common type definitions
│   │
│   ├── nodes/                      # All workflow nodes
│   │   ├── __init__.py
│   │   │
│   │   ├── shared/                 # Reusable nodes (cross-workflow)
│   │   │   ├── __init__.py
│   │   │   ├── email_nodes.py      # EmailDrafter, EmailSender, EmailParser
│   │   │   ├── calendar_nodes.py   # FetchAvailability, CreateEvent
│   │   │   ├── decision_nodes.py   # Classifiers, Routers
│   │   │   └── retrieval_nodes.py  # ContextRetriever, HistoryFetcher
│   │   │
│   │   └── specialized/            # Workflow-specific nodes
│   │       ├── __init__.py
│   │       ├── meeting_nodes.py    # ExtractMeetingDetails, FindSlots
│   │       ├── support_nodes.py    # CategorizeIssue, CreateTicket
│   │       └── sales_nodes.py      # ScoreLead, UpdateCRM
│   │
│   ├── workflows/                  # Workflow definitions (LangGraph)
│   │   ├── __init__.py
│   │   ├── meeting_scheduler.py    # Meeting scheduling workflow
│   │   ├── support_ticket.py       # Support ticket workflow
│   │   ├── auto_responder.py       # General auto-response workflow
│   │   └── router.py               # Workflow router (intent → workflow)
│   │
│   ├── integrations/               # External service integrations
│   │   ├── __init__.py
│   │   ├── email/
│   │   │   ├── __init__.py
│   │   │   ├── gmail.py            # Gmail API
│   │   │   ├── outlook.py          # Outlook API
│   │   │   └── imap.py             # Generic IMAP
│   │   ├── calendar/
│   │   │   ├── __init__.py
│   │   │   ├── google.py           # Google Calendar
│   │   │   └── outlook.py          # Outlook Calendar
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   └── client.py           # LLM client (OpenAI/Anthropic)
│   │   └── crm/                    # Optional: CRM integrations
│   │       ├── __init__.py
│   │       └── salesforce.py
│   │
│   ├── memory/                     # Persistence layer
│   │   ├── __init__.py
│   │   ├── vector_store.py         # Vector DB for email history
│   │   ├── cache.py                # Redis/in-memory cache
│   │   └── checkpointer.py         # LangGraph state persistence
│   │
│   ├── engine/                     # Main orchestration (NOT multi-agent)
│   │   ├── __init__.py
│   │   ├── processor.py            # EmailProcessor - main entry point
│   │   └── scheduler.py            # Background job scheduler
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py               # Logging
│   │   ├── validators.py           # Input validation
│   │   ├── formatters.py           # Text formatting
│   │   └── retry.py                # Retry logic
│   │
│   └── cli/                        # Command-line interface
│       ├── __init__.py
│       └── main.py                 # CLI commands (Click/Typer)
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures
│   │
│   ├── unit/
│   │   ├── test_nodes/
│   │   │   ├── test_email_nodes.py
│   │   │   └── test_meeting_nodes.py
│   │   └── test_workflows/
│   │       ├── test_meeting_scheduler.py
│   │       └── test_support_ticket.py
│   │
│   ├── integration/
│   │   └── test_end_to_end.py
│   │
│   ├── fixtures/                   # Test data
│   │   └── emails/
│   │       ├── meeting_request.eml
│   │       ├── support_issue.eml
│   │       └── sales_inquiry.eml
│   │
│   └── mocks/
│       ├── mock_email_client.py
│       └── mock_llm.py
│
├── data/
│   ├── vector_db/                  # Chroma/FAISS storage
│   ├── cache/                      # Temporary cache
│   ├── logs/                       # Application logs
│   └── checkpoints/                # Workflow state checkpoints
│
├── scripts/
│   ├── run.py                      # Main entry point
│   ├── setup_db.py                 # Initialize vector store
│   └── test_connection.py          # Test email/calendar connections
│
└── docs/
    ├── architecture.md
    ├── workflows/
    │   ├── meeting_scheduler.md
    │   └── support_ticket.md
    └── setup.md
```