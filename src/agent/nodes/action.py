from src.agent.tools.registry import ALL_TOOLS_BY_NAME
from langchain_core.messages import ToolMessage


async def action_node(state):
    """Performs the tool call"""
    result = []
    state_updates = {}

    for tool_call in state["messages"][-1].tool_calls:
        tool = ALL_TOOLS_BY_NAME[tool_call["name"]]
        observation = await tool.ainvoke(tool_call["args"])
        
        # draft and send handle
        if tool_call["name"] == "draft_email":
            if isinstance(observation, dict) and observation.get("approved"):
                state_updates["draft_approved"] = True
            else:
                state_updates["draft_approved"] = False

        if tool_call["name"] == "send_email":
            state_updates["draft_approved"] = False  # reset after send

        result.append(
            ToolMessage(
                content=observation,
                tool_call_id=tool_call["id"]
            )
        )

    return {"messages": result, **state_updates}
