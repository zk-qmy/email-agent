from langgraph.checkpoint.memory import MemorySaver

_checkpointer_instance = None


def get_checkpointer() -> MemorySaver:
    """Singleton checkpointer. Swap MemorySaver → Postgres/Redis here only."""
    global _checkpointer_instance
    if _checkpointer_instance is None:
        _checkpointer_instance = MemorySaver()
        try:
            _checkpointer_instance.serde.allowed_msgpack_modules.add(
                ("src.core.states", "EmailData")
            )
            _checkpointer_instance.serde.allowed_msgpack_modules.add(
                ("src.core.states", "MeetingData")
            )
        except AttributeError:
            pass  # older LangGraph versions don't expose this
    return _checkpointer_instance
