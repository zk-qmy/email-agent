from langgraph.graph import END, START, StateGraph
from src.workflows.scheduling.state import AgentState
from src.memory.checkpointer import get_checkpointer
from src.nodes.shared.decision_nodes import classify_workflow
from src.workflows.scheduling.edges import build_meeting_graph
# from src.workflows.support_ticket import build_support_graph  ← add when ready


def _route_workflow(state: AgentState) -> str:
    if state.workflow == "schedule":
        return "meeting_flow"
    # elif state.workflow == "ticket":
    #     return "support_flow"
    return END


def build_router():
    """Root graph. Owns the checkpointer — subgraphs are compiled without one.

    To add a workflow:
      1. Uncomment (or add) the import above
      2. Add: builder.add_node("new_flow", build_new_graph())
      3. Add the return value to _route_workflow and the conditional edges
      4. Add: builder.add_edge("new_flow", END)
    """
    builder = StateGraph(AgentState)

    builder.add_node("classify", classify_workflow)
    builder.add_node("meeting_flow", build_meeting_graph())
    # builder.add_node("support_flow", build_support_graph())

    builder.add_edge(START, "classify")
    builder.add_conditional_edges("classify", _route_workflow, {
        "meeting_flow": "meeting_flow",
        # "support_flow": "support_flow",
        END: END,
    })
    builder.add_edge("meeting_flow", END)
    # builder.add_edge("support_flow", END)

    return builder.compile(checkpointer=get_checkpointer())
