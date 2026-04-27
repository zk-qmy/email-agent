from langgraph.graph import StateGraph, END
from src.agent.state import AgentState
from src.agent.nodes.reasoning import reasoning_node
from src.agent.nodes.action import action_node
from src.agent.config import get_checkpointer
from datetime import datetime
import os


def route(state):
    return END if state["next_action"] == "final" else "action"


def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("reasoning", reasoning_node)
    workflow.add_node("action", action_node)
    workflow.set_entry_point("reasoning")
    workflow.add_conditional_edges("reasoning", route, {"action": "action", END: END})
    workflow.add_edge("action", "reasoning")
    return workflow.compile(checkpointer=get_checkpointer())


def save_graph(graph):
    # Print Image
    filename = datetime.now().strftime(
        "agent_graph_%Y%m%d_%H%M%S.png")

    os.makedirs("assets/graph", exist_ok=True)
    png_data = graph.get_graph(xray=True).draw_mermaid_png()
    with open(f"assets/graph/{filename}", "wb") as f:
        f.write(png_data)
    print(f"Saved to assets/graph/{filename}")
    return
