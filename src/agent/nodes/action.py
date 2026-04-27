from langgraph.types import interrupt
from src.agent.config import SENSITIVE_ACTIONS
from src.agent.tools.registry import TOOLS


def action_node(state):
    action = state["action"]
    action_input = state["action_input"]

    if action in SENSITIVE_ACTIONS:
        user_decision = interrupt(
            {
                "question": f"Approve '{action}' with input: {action_input}?",
                "action": action,
                "action_input": action_input,
            }
        )
        if not user_decision.get("approved", False):
            return {
                "messages": [f"Observation: Action '{action}' was cancelled."],
                "next_action": "reasoning",
                "iteration_count": state["iteration_count"] + 1,
            }
        action_input = user_decision.get("action_input", action_input)

    if action not in TOOLS:
        return {
            "messages": [f"Observation: Unknown tool '{action}'"],
            "next_action": "reasoning",
            "iteration_count": state["iteration_count"] + 1,
        }

    result = TOOLS[action](action_input)
    return {
        "messages": [f"Observation: {result}"],
        "next_action": "reasoning",
        "iteration_count": state["iteration_count"] + 1,
    }
