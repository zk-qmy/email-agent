from dataclasses import dataclass, field
from config.tool_prompts.base import NodePrompt, PromptConfig
from config.tool_prompts.system_prompt import SystemPrompt
from datetime import datetime


@dataclass
class EmailPrompts(PromptConfig):
    """
    Prompts for the meeting scheduler workflow.
    Each field corresponds to one node's prompt.
    You can add custom fields as needed.
    The NodePrompt parts (system/context/task/critic) can use $variable substitution.
    """

    summarize_email: NodePrompt = field(
        default_factory=lambda: NodePrompt(
            system=SystemPrompt.system_prompt,
            context=(
                "Email thread details (chronological order, latest first):\n"
                "  Subject: $subject\n"
                "$email_list"
            ),
            task=(
                "Summarize the email thread in CONTEXT into a concise and structured format.\n"
                "Format:\n"
                "  Subject: <thread subject>\n"
                "  Participants: <participant list>\n"
                "  Email Count: <number of emails>\n"
                "  Conversation Flow:\n"
                "    - <chronological summary of each email or phase>\n"
                "    - <...>\n"
                "  Summary: <1-2 sentence overview>\n"
                "  Key Points:\n"
                "    - <bullet 1>\n"
                "    - <bullet 2>\n"
                "    - <bullet 3 (if needed)>\n"
                "  Action Items (if any):\n"
                "    - <action 1>\n"
                "    - <action 2>\n\n"
                "Rules:\n"
                "- Show the conversation flow in chronological order from oldest to newest\n"
                "- Keep the summary concise (maximum 2 sentences)\n"
                "- Extract only the most important points from the thread\n"
                "- Do not add information that is not in the emails\n"
                "- Use short bullet points for Key Points\n"
                "- Maximum 3 key points\n"
                "- Maintain a professional and neutral tone"
            ),
            critic=(
                "Verify:\n"
                "- Conversation flow is in chronological order\n"
                "- Summary captures the overall thread, not just one email\n"
                "- Key Points are relevant and concise\n"
                "- No hallucinated or extra information\n"
                "- Output strictly follows the required format\n"
                "- Tone is neutral and professional"
            ),
        )
    )

    # extract_meeting_info: NodePrompt = field(
    #     default_factory=lambda: NodePrompt(
    #         system=SystemPrompt.system_prompt,
    #         context=(
    #             "Today's date is: $today\n"
    #             "Already extracted so far:\n"
    #             "  Date: $date\n"
    #             "  Time: $time\n"
    #             "  Participants: $participants\n"
    #             "Only extract fields that are missing or updated in the new message."
    #         ),
    #         task=(
    #             "Extract meeting information from the conversation.\n"
    #             "- Return date as YYYY-MM-DD format.\n"
    #             "- If the date is relative (like 'next Monday', 'this Friday', 'tomorrow'), "
    #             "interpret it relative to today's date provided in CONTEXT.\n"
    #             "- Time should be in HH:MM format.\n"
    #             "- Participants should be names or emails."
    #         ),
    #         critic=(
    #             "Verify:\n"
    #             "- No invented values not stated by the user\n"
    #             "- participants is a list, not a string\n"
    #             "- Null fields are truly null, not empty string"
    #         ),
    #     )
    # )

    draft_meeting_email: NodePrompt = field(
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
                "- If CC or BCC recipients are specified elsewhere, acknowledge them in the email body if appropriate (e.g., 'I've CC'd ...')"
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
    draft_general_email: NodePrompt = field(
        default_factory=lambda: NodePrompt(
            system=SystemPrompt.system_prompt,
            context=(
                "Email details:\n"
                "  Recipient:   $recipient\n"
                "  Purpose:     $purpose\n"
                "  Key points:  $key_points\n"
                "  Tone:        $tone"
            ),
            task=(
                "Draft a professional email using the details in CONTEXT.\n"
                "Format:\n"
                "  Subject: <subject line>\n\n"
                "  <body — 3 to 5 sentences max>\n\n"
                "  Best regards\n\n"
                "Rules:\n"
                "- Write the subject line as the first line, prefixed with 'Subject:'\n"
                "- Cover all key points from CONTEXT naturally in the body\n"
                "- Match the tone specified in CONTEXT\n"
                "- No placeholder text like [Name] or [Details] or $recipient, $date, or $time\n"
                "- If the user has specified requirements, follow them (e.g., tone, length, specific phrases)\n"
                "- If CC or BCC recipients are specified elsewhere, acknowledge them in the email body if appropriate (e.g., 'I've CC'd ...')"
            ),
            critic=(
                "Verify:\n"
                "- Subject line is present and starts with 'Subject:'\n"
                "- All key points from CONTEXT are addressed in the body\n"
                "- Tone matches what was specified\n"
                "- No placeholder text\n"
                "- Sign-off is included\n"
                "- Body is 3 to 5 sentences, not longer\n"
                "- Any specific user requirements are followed"
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


email_prompts = EmailPrompts()

"""
Example usage:

"""
