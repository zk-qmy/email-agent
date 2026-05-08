from dataclasses import dataclass, field
from config.tool_prompts.base import NodePrompt, PromptConfig
from config.tool_prompts.system_prompt import SystemPrompt
from datetime import datetime


@dataclass
class FilePrompts(PromptConfig):
    """
    Prompts for processing files such as PDF, images.
    Each field corresponds to one node's prompt.
    You can add custom fields as needed.
    The NodePrompt parts (system/context/task/critic) can use $variable substitution.
    """

    check_pdf_form_completion: NodePrompt = field(
    default_factory=lambda: NodePrompt(
        system=SystemPrompt.system_prompt,
        context=(
            "Form content:\n"
            "$text\n\n"
            "User role:\n"
            "$role\n"
        ),
        task=(
            "Analyze the form in CONTEXT and identify all fields that require input.\n\n"
            
            "Classify each field into:\n"
            "- required_fields: must be filled by the user role\n"
            "- optional_fields: can be left empty\n"
            "- not_user_fields: fields not meant for this user role\n\n"

            "Then check which required fields are missing.\n\n"

            "Return the result in JSON format:\n"
            "{\n"
            '  "required_fields": ["..."],\n'
            '  "optional_fields": ["..."],\n'
            '  "not_user_fields": ["..."],\n'
            '  "missing_fields": ["..."],\n'
            '  "message_to_user": "<clear instruction asking user to fill missing fields>"\n'
            "}\n\n"

            "Rules:\n"
            "- Use the form structure and labels to determine fields\n"
            "- Required fields are those the student must complete before submission\n"
            "- Fields labeled optional or clearly for advisor/office are NOT required\n"
            "- Do NOT guess values\n"
            "- If a required field is empty or blank, include it in missing_fields\n"
            "- message_to_user must clearly list what the user needs to fill\n"
            "- Output must be valid JSON only"
        ),
        critic=(
            "Verify:\n"
            "- All fields are correctly classified\n"
            "- Required vs optional vs non-user fields are logical\n"
            "- Missing fields include all empty required fields\n"
            "- message_to_user is clear and helpful\n"
            "- Output is valid JSON\n"
        ),
    )
)


file_prompts = FilePrompts()
