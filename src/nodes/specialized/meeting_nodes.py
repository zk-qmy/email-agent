from langgraph.types import interrupt
from pydantic import BaseModel
from src.core.states import AgentState, MeetingData
from src.integrations.llm.client import get_llm


class MeetingExtraction(BaseModel):
    date: str | None = None
    time: str | None = None
    participants: list[str] | None = None


def extract_meeting_info(state: AgentState) -> dict:
    result = get_llm().with_structured_output(MeetingExtraction).invoke([
        {
            "role": "system",
            "content": (
                "Extract meeting information from the conversation.\n"
                "Return date (YYYY-MM-DD if possible), time (HH:MM), "
                "and participants (emails if possible)."
            ),
        },
        {
            "role": "user",
            "content": state.messages[-1]["content"]
        },
    ])
    # Merge onto existing state — never wipe values from a previous turn
    updated = MeetingData(
        date=result.date or state.meeting.date,
        time=result.time or state.meeting.time,
        participants=result.participants or state.meeting.participants,
        missing_fields=state.meeting.missing_fields,
    )
    print(f"[extract_meeting_info] date={updated.date}, time={updated.time}, participants={updated.participants}")
    return {"meeting": updated}


def check_missing_fields(state: AgentState) -> dict:
    missing = []
    if not state.meeting.date:
        missing.append("date")
    if not state.meeting.time:
        missing.append("time")
    if not state.meeting.participants:
        missing.append("participants")
    print(f"[check_missing_fields] missing: {missing}")
    # Return full MeetingData to avoid wiping existing values
    return {
        "meeting": MeetingData(
            date=state.meeting.date,
            time=state.meeting.time,
            participants=state.meeting.participants,
            missing_fields=missing,
        )
    }


def ask_for_missing_info(state: AgentState) -> dict:
    question = ("I still need the following information: "
                + ", ".join(state.meeting.missing_fields)
                + ".")
    print(f"[ask_for_missing_info] {question}")
    user_reply = interrupt({"message": question})

    # Append the user's reply to messages so extract_meeting_info sees new input.
    updated_messages = state.messages + [user_reply]
    return {"messages": updated_messages, "response": question}


def book_calendar(state: AgentState) -> dict:
    confirmation = f"Meeting confirmed and booked on {state.meeting.date} at {state.meeting.time}."
    print(f"[book_calendar] {confirmation}")
    return {"response": confirmation}
