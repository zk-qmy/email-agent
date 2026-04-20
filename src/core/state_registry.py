from src.workflows.ticket.state import TicketState
from src.workflows.scheduling.state import ScheduleState
from src.workflows.chat.state import ChatState  # <-- replace with actual ChatState when ready

_STATE_SCHEMAS = {
    "schedule": ScheduleState,
    "ticket": TicketState,
    "chat": ChatState,  # <-- replace with actual ChatState when ready
    # Add more workflows and their corresponding state schemas here
}


def get_state_schema(workflow_name: str):
    return _STATE_SCHEMAS.get(workflow_name, "BaseState")
