from dataclasses import dataclass, field
from config.prompts.base import NodePrompt, PromptConfig
from config.prompts.system_prompt import SystemPrompt
from datetime import datetime


@dataclass
class TicketPrompts(PromptConfig):
    """
    Prompts for the ticket handling workflow.
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

    extract_ticket_info: NodePrompt = field(
        default_factory=lambda: NodePrompt(
            system=SystemPrompt.system_prompt,
            context=(
                ""
            ),
            task=(
                "Extract academic accommodation (AA) request details from the message.\n"
                "Fields: student_name, student_id, gpa (float), credits_completed (int), "
                "reason for AA, advisor_email, registrar_email.\n"
                "Return None for any field not mentioned."

            ),
            critic=(
                ""
            ),
        )
    )

    draft_email: NodePrompt = field(
        default_factory=lambda: NodePrompt(
            system=SystemPrompt.system_prompt,
            context=(
                "Ticket details:\n"
                "  Student Name: $student_name\n"
                "  Student ID: $student_id\n"
                "  GPA: $gpa\n"
                "  Credits Completed: $credits_completed\n"
                "  Reason for AA: $reason_for_aa\n"
                "  Advisor Email: $advisor_email\n"
                "  Registrar Email: $registrar_email"
            ),
            task=(
                "You are an academic assistant helping a student submit an "
                "Academic Accommodation (AA) request.\n"
                "Draft a professional email from the student to their academic advisor "
                "requesting the AA. Include a brief Form Summary at the end.\n"
                "Be concise, polite, and professional."

            ),
            critic=(
                "Verify:\n"
                "- Subject line is present and starts with 'Subject:'\n"
                "- Date and time from CONTEXT appear in the body\n"
                "- No placeholder text\n"
                "- Sign-off is included\n"
                "- Body is 5 to 10 sentences, not longer"
            ),
        )
    )

    classify_advisor_reply: NodePrompt = field(
        default_factory=lambda: NodePrompt(
            system=SystemPrompt.system_prompt,
            task=(
                "Classify an advisor's reply to an AA request as one of:\n"
                "- approved    (advisor approves)\n"
                "- needs_info  (advisor needs more information)\n"
                "- rejected    (advisor denies)\n"
                "Return structured output only."

            ),
            critic=("""        """),
        )
    )

    classify_registrar_reply: NodePrompt = field(
        default_factory=lambda: NodePrompt(
            system=SystemPrompt.system_prompt,
            task=(
                "Classify a registrar's reply to an AA request as one of:\n"
                "- approved        (registrar fully processes the request)\n"
                "- issue_detected  (registrar found a problem or missing item)\n"
                "Return structured output only."


            ),
            critic=("""        """),
        )
    )


ticket_prompts = TicketPrompts()

"""
Example usage:

"""
