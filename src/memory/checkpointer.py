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
        cp = MemorySaver()
        _configure_serde(cp)
        _checkpointer_instance = cp

    return _checkpointer_instance
