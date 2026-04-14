from datetime import datetime
from typing import Optional, List, cast
from langgraph.types import interrupt
from pydantic import BaseModel
from src.workflows.scheduling.state import MeetingData, ScheduleState
from src.integrations.llm.client import get_llm
from config.prompts.scheduling import meeting_prompts
from config.prompts.base import PromptConfig


class MeetingExtraction(BaseModel):
    date: Optional[str] = None
    time: Optional[str] = None
    participants: Optional[List[str]] = None


def extract_meeting_info(state: ScheduleState,
                         prompt_config: PromptConfig = meeting_prompts
                         ) -> dict:
    messages = state.messages if hasattr(state, "messages") else []
    last_message = messages[-1]["content"] if messages else ""

    prompt = prompt_config.get("extract_meeting_info")
    message_prompt = prompt.build_messages(
        user_content=last_message,
        today=datetime.now().strftime("%Y-%m-%d"),
        date=state.meeting.date or "not yet provided",
        time=state.meeting.time or "not yet provided",
        participants=", ".join(
            state.meeting.participants) or "not yet provided",
    )

    result = (
        get_llm()
        .with_structured_output(MeetingExtraction)
        .invoke(message_prompt)
    )
    '''
    result = (
        get_llm()
        .with_structured_output(MeetingExtraction)
        .invoke(
            [
                {
                    "role": "system",
                    "content": (
                        f"Extract meeting information from the conversation.\n"
                        f"Today's date is: {today}\n"
                        f"- Return date as YYYY-MM-DD format.\n"
                        f"- If the date is relative (like 'next Monday', 'this Friday', 'tomorrow'), "
                        f"interpret it relative to today's date ({today}) and return the resolved YYYY-MM-DD date.\n"
                        f"- Time should be in HH:MM format.\n"
                        f"- Participants should be names or emails."
                    ),
                },
                {"role": "user", "content": last_message},
            ]
        )
    )
    '''

    existing_meeting = state.meeting if hasattr(
        state, "meeting") else MeetingData()

    extracted = cast(MeetingExtraction, result)
    updated = MeetingData(
        date=extracted.date or getattr(existing_meeting, "date", None),
        time=extracted.time or getattr(existing_meeting, "time", None),
        participants=extracted.participants
        or getattr(existing_meeting, "participants", []),
        missing_fields=getattr(existing_meeting, "missing_fields", []),
    )
    print(
        f"[extract_meeting_info] date={updated.date}, time={updated.time}, participants={updated.participants}"
    )
    return {"meeting": updated}


def check_missing_fields(state: ScheduleState) -> dict:
    meeting = state.meeting if hasattr(state, "meeting") else MeetingData()

    missing = []
    if not meeting.date:
        missing.append("date")
    if not meeting.time:
        missing.append("time")
    if not meeting.participants:
        missing.append("participants")

    print(f"[check_missing_fields] missing: {missing}")
    return {
        "meeting": MeetingData(
            date=meeting.date,
            time=meeting.time,
            participants=meeting.participants,
            missing_fields=missing,
        )
    }


def ask_for_missing_info(state: ScheduleState) -> dict:
    meeting = state.meeting if hasattr(state, "meeting") else MeetingData()
    missing = meeting.missing_fields if hasattr(
        meeting, "missing_fields") else []

    if not missing:
        missing_str = "required information"
    else:
        missing_str = ", ".join(missing)

    question = f"I need the following information: {missing_str}. Please provide these details."
    print(f"[ask_for_missing_info] {question}")

    user_reply = interrupt(
        {
            "type": "missing_fields",
            "message": question,
            "missing_fields": missing,
            "email_draft": None,
            "data": {
                "current_date": meeting.date,
                "current_time": meeting.time,
                "current_participants": meeting.participants,
            },
        }
    )

    user_content = (
        user_reply.get("content", "")
        if isinstance(user_reply, dict)
        else str(user_reply)
    )

    return {"messages": state.messages + [{"role": "user", "content": user_content}]}


def book_calendar(state: ScheduleState) -> dict:
    meeting = state.meeting if hasattr(state, "meeting") else MeetingData()
    date = getattr(meeting, "date", None)
    time = getattr(meeting, "time", None)

    confirmation = f"Meeting confirmed and booked on {date} at {time}."
    print(f"[book_calendar] {confirmation}")
    return {"response": confirmation}
