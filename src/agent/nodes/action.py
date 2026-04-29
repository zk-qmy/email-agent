from src.agent.tools.email_tools import ALL_TOOLS_BY_NAME
from langchain_core.messages import ToolMessage


def action_node(state):
    """Performs the tool call"""
    result = []
    state_updates = {}

    for tool_call in state["messages"][-1].tool_calls:
        tool = ALL_TOOLS_BY_NAME[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])

        # Save approved draft to state so reasoning node can access it
        if tool_call["name"] == "draft_email":
            state_updates["approved_draft"] = observation
            state_updates["draft_approved"] = True

        # Clear approval flag after send attempt
        if tool_call["name"] == "send_email":
            state_updates["draft_approved"] = False
            state_updates["approved_draft"] = ""

        result.append(
            ToolMessage(
                content=observation,
                tool_call_id=tool_call["id"]
            )
        )

    return {"messages": result, **state_updates}
