from src.workflows.scheduling.graph import build_meeting_graph
from src.workflows.ticket.graph import build_ticket_graph

_GRAPHS = {}


async def startup():
    """Call this explicitly on app startup, not at import time."""
    _GRAPHS["schedule"] = build_meeting_graph()
    _GRAPHS["ticket"] = build_ticket_graph()


def get_graph(workflow_name: str):
    if not _GRAPHS:
        raise RuntimeError("Graphs not compiled. Call startup() first.")
    graph = _GRAPHS.get(workflow_name)
    if graph is None:
        raise ValueError(
            f"Unknown workflow: {workflow_name!r}. "
            f"Available: {list(_GRAPHS.keys())}"
        )
    return graph


def classify_workflow(user_message: str) -> str:
    from src.integrations.llm.client import get_llm
    from pydantic import BaseModel
    from typing import Literal
    from config.prompts.scheduling import meeting_prompts as prompt_config

    class WorkflowOutput(BaseModel):
        workflow: Literal["schedule", "ticket"]

    llm = get_llm()
    structured_llm = llm.with_structured_output(WorkflowOutput)

    prompt = prompt_config.get("classify_workflow")
    messages = prompt.build_messages(
        user_content=user_message)  # pass actual message

    result = structured_llm.invoke(messages)
    return result.workflow
