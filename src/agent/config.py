# config.py
from langchain_core.callbacks import BaseCallbackHandler
import logging


class ToolLogger(BaseCallbackHandler):
    def on_tool_start(self, tool, input_str, **kwargs):
        logging.info(f"TOOL START  {tool['name']} | input: {input_str}")

    def on_tool_end(self, output, **kwargs):
        logging.info(f"TOOL END    output: {output[:120]}")

    def on_tool_error(self, error, **kwargs):
        logging.error(f"TOOL ERROR  {error}")


# Add action names here to require human approval before execution
SENSITIVE_ACTIONS = {"send_email", "schedule_meeting"}


def get_checkpointer():
    # DEV — lost on restart, no setup needed
    from langgraph.checkpoint.memory import MemorySaver

    return MemorySaver()

    # PROD — persists across restarts
    # from langgraph.checkpoint.sqlite import SqliteSaver

    # return SqliteSaver.from_conn_string("checkpoints.db")
