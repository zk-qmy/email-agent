# state.py
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    draft_approved: bool


def initial_state(user_message: str) -> AgentState:
    return {
        "messages": [HumanMessage(content=user_message)],
    }
