"""
extract_meeting_info
check_missing_fields???
ask_for _missing _info?
draft
followup
extract_intent
write_noti
"""

from dataclasses import dataclass, field
from config.prompts.base import NodePrompt, PromptConfig
from config.prompts.system_prompt import SystemPrompt
from datetime import datetime


@dataclass
class MeetingSchedulerPrompts(PromptConfig):
    """
    Prompts for the meeting scheduler workflow.
    Each field corresponds to one node's prompt.
    You can add custom fields as needed.
    The NodePrompt parts (system/context/task/critic) can use $variable substitution.
    """

    classify: NodePrompt = field(
        default_factory=lambda: NodePrompt(
            system=SystemPrompt.system_prompt,
            task=(
                """
        """
            ),
            critic=("""        """),
        )
    )

    extract_meeting_info: NodePrompt = field(
        default_factory=lambda: NodePrompt(
            system=SystemPrompt.system_prompt,
            context=(
                "Today's date is: $today\n"
                "Already extracted so far:\n"
                "  Date: $date\n"
                "  Time: $time\n"
                "  Participants: $participants\n"
                "Only extract fields that are missing or updated in the new message."
            ),
            task=(
                "Extract meeting information from the conversation.\n"
                "- Return date as YYYY-MM-DD format.\n"
                "- If the date is relative (like 'next Monday', 'this Friday', 'tomorrow'), "
                "interpret it relative to today's date provided in CONTEXT.\n"
                "- Time should be in HH:MM format.\n"
                "- Participants should be names or emails."
            ),
            critic=(
                "Verify:\n"
                "- No invented values not stated by the user\n"
                "- participants is a list, not a string\n"
                "- Null fields are truly null, not empty string"
            ),
        )
    )

    draft_email: NodePrompt = field(
        default_factory=lambda: NodePrompt(
            system=SystemPrompt.system_prompt,
            context=(
                "Meeting details:\n"
                "  Recipient: $recipient\n"
                "  Date:      $date\n"
                "  Time:      $time\n"
                "  Purpose:   $purpose"
            ),
            task=(
                "Draft a professional meeting request email using the details in CONTEXT.\n"
                "Format:\n"
                "  Subject: <subject line>\n\n"
                "  <body — 2 to 3 sentences max>\n\n"
                "  Best regards\n\n"
                "Rules:\n"
                "- Use the exact date and time from CONTEXT\n"
                "- No placeholder text like [Name] or [Date]\n"
                "- Write the subject line as the first line, prefixed with 'Subject:'"
                "- If the user has specify requirements make sure to follow it (e.g., tone, length, specific phrases)"
            ),
            critic=(
                "Verify:\n"
                "- Subject line is present and starts with 'Subject:'\n"
                "- Date and time from CONTEXT appear in the body\n"
                "- No placeholder text\n"
                "- Sign-off is included\n"
                "- Body is 2 to 3 sentences, not longer"
                "- Make sure to follow any specific user requirements (e.g., tone, length, specific phrases)"
            ),
        )
    )

    reply_intent: NodePrompt = field(
        default_factory=lambda: NodePrompt(
            system=SystemPrompt.system_prompt,
            task=(
                """
            Determine the intent of the user's reply to the email (e.g., approve, request changes, ask a question).
            """
            ),
            critic=("""        """),
        )
    )

    """
    check_missing_fields???
    ask_for _missing _info?
    draft
    followup
    extract_intent
    write_notification
    """


meeting_prompts = MeetingSchedulerPrompts()

"""
Example usage:

"""
