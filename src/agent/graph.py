# graph.py
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode  # ← replaces action_node entirely
from langchain_core.messages import HumanMessage
from src.agent.state import AgentState
from src.agent.nodes.reasoning import reasoning_node
from src.agent.tools.registry import ALL_TOOLS
from src.agent.config import get_checkpointer
import os
from datetime import datetime


def route(state):
    messages = state.get("messages", [])
    if not messages:
        return END
    last = messages[-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("reasoning", reasoning_node)
    workflow.add_node("tools", ToolNode(ALL_TOOLS, handle_tool_errors=True))
    workflow.set_entry_point("reasoning")
    workflow.add_conditional_edges("reasoning", route, {"tools": "tools", END: END})
    workflow.add_edge("tools", "reasoning")
    return workflow.compile(checkpointer=get_checkpointer())


def save_graph(graph):
    # Print Image
    filename = datetime.now().strftime("agent_graph_%Y%m%d_%H%M%S.png")

    os.makedirs("assets/graph", exist_ok=True)
    png_data = graph.get_graph(xray=True).draw_mermaid_png()
    with open(f"assets/graph/{filename}", "wb") as f:
        f.write(png_data)
    print(f"Saved to assets/graph/{filename}")
    return
