# Add action names here to require human approval before execution
SENSITIVE_ACTIONS = {"send_email", "schedule_meeting"}


def get_checkpointer():
    # DEV — lost on restart, no setup needed
    from langgraph.checkpoint.memory import MemorySaver
    return MemorySaver()

    # PROD — persists across restarts
    #from langgraph.checkpoint.sqlite import SqliteSaver

    #return SqliteSaver.from_conn_string("checkpoints.db")
