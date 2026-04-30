# state.py
from typing import Annotated
from typing import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages  # handles append + dedup


class AgentState(TypedDict):
    messages:        Annotated[list[BaseMessage], add_messages]
    approved_draft: str
    draft_approved: bool = False


def initial_state(user_message: str) -> AgentState:
    from langchain_core.messages import HumanMessage
    return {
        "messages": [HumanMessage(content=user_message)],
    }
