from typing import TypedDict, Annotated
import operator


class AgentState(TypedDict):
    messages: Annotated[list, operator.add]  # append-only
    next_action: str
    iteration_count: int
    thought: str
    action: str
    action_input: str


def initial_state(user_message: str) -> AgentState:
    print(f"User input: {user_message}")
    return {
        "messages": [f"User: {user_message}"],
        "next_action": "",
        "iteration_count": 0,
        "thought": "",
        "action": "",
        "action_input": "",
    }
