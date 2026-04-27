from .graph import build_agent_graph
from src.db.checkpointer import get_checkpointer


_graph = None


async def get_graph():
    global _graph
    if _graph is None:
        cp = await get_checkpointer()
        _graph = build_agent_graph().compile(checkpointer=cp)
    return _graph
