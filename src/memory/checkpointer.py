from langgraph.checkpoint.memory import MemorySaver

_checkpointer_instance = None


def _configure_serde(cp: MemorySaver):
    modules = {
        ("src.core.states", "EmailData"),
        ("src.core.states", "MeetingData"),
    }

    if hasattr(cp, "serde"):
        current = getattr(cp.serde, "allowed_msgpack_modules", set())
        cp.serde.allowed_msgpack_modules = current.union(modules)
    else:
        print("[WARN] No serde support — custom state may break in future")


def get_checkpointer() -> MemorySaver:
    global _checkpointer_instance

    if _checkpointer_instance is None:
        _checkpointer_instance = MemorySaver()
        try:
            _checkpointer_instance.serde.allowed_msgpack_modules.add(  # type: ignore[attr-defined]
                ("src.core.states", "EmailData")
            )
            _checkpointer_instance.serde.allowed_msgpack_modules.add(  # type: ignore[attr-defined]
                ("src.core.states", "MeetingData")
            )
        except AttributeError:
            pass  # older LangGraph versions don't expose this
    return _checkpointer_instance
