import asyncio
from typing import Dict, Any
from langgraph.types import Command
from src.app.sessions.conversation import ConversationSession
from src.workflows.registry import get_graph, classify_workflow
from pydantic import BaseModel

class SessionManager:
    def __init__(self):
        self._sessions: Dict[str, ConversationSession] = {}

    # ── Public API ───────────────────────────────────────────────────

    async def handle_message(
        self,
        conversation_id: str,
        user_message:    dict,
        workflow_name:   str | None = None,
    ) -> dict:
        """
        Main entry point. Called once per user message.
        Creates a session on first call; resumes interrupt on subsequent calls.
        """
        session = self._sessions.get(conversation_id)

        if session is None:
            # First message in this conversation — classify and create session
            if workflow_name is None:
                workflow_name = classify_workflow(user_message["content"])
            session = ConversationSession(
                conversation_id=conversation_id,
                workflow_name=workflow_name,
            )
            self._sessions[conversation_id] = session

        graph = get_graph(session.workflow_name)
        config = {
            "configurable": {"thread_id": conversation_id},
            "recursion_limit": 40,
        }

        if session.status == "waiting_interrupt":
            payload = Command(resume=user_message)
        else:
            payload = self._build_initial_state(
                session.workflow_name, user_message)

        session.status = "running"

        # Run as its own asyncio task — does not block other conversations
        session.task = asyncio.create_task(
            self._run(session, graph, payload, config)
        )
        return await session.task

    def get_status(self, conversation_id: str) -> str:
        s = self._sessions.get(conversation_id)
        return s.status if s else "not_found"

    # ── Private helpers ──────────────────────────────────────────────

    async def _run(self, session, graph, payload, config) -> dict:
        try:
            result = await graph.ainvoke(payload, config)
            if "__interrupt__" in result:
                session.status = "waiting_interrupt"
            else:
                session.status = "done"
            return result
        except Exception as e:
            session.status = "error"
            print(f"[SessionManager] Error in conversation {session.conversation_id}: {e}")
            raise

    def _build_initial_state(self, workflow_name: str, user_message: dict) -> dict:
        base = {
            "conversation_id": "",   # filled by caller / API layer
            "messages": [user_message],
            "workflow": workflow_name,
            "response": None,
        }
        if workflow_name == "schedule":
            from src.workflows.scheduling.state import MeetingData, EmailData
            return {**base, "meeting": MeetingData(), "email": EmailData()}
        if workflow_name == "ticket":
            from src.workflows.ticket.state import RequestData, EmailData
            return {**base, "aa_request": RequestData(),
                    "aa_email": EmailData(), "registrar_email": EmailData()}
        return base
