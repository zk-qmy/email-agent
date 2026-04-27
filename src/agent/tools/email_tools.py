# tools/email_tools.py
from src.integrations.llm.client import get_llm
from src.agent.utils import extract_text

from config.prompts.email import meeting_prompts


# def draft_email_tool(context: str) -> str:
#     prompt = meeting_prompts.get("draft_email")

#     messages = prompt.build_messages(
#         context=context
#     )
#     response = get_llm().invoke(messages)
#     return extract_text(response)


def draft_email_tool(action_input: str) -> str:
    llm = get_llm()

    # Step 1 — extract structured fields from action_input via LLM
    extraction_prompt = f"""
                        Extract these fields from the text below. Reply ONLY with raw JSON, no fences.
                        {{
                        "recipient": "...",
                        "date":      "...",
                        "time":      "...",
                        "purpose":   "..."
                        }}

                        If a field is missing, use "not specified".

                        Text: {action_input}
                        """
    raw = extract_text(llm.invoke(extraction_prompt))

    import json, re

    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
    try:
        fields = json.loads(raw)
    except json.JSONDecodeError:
        fields = {
            "recipient": "not specified",
            "date": "not specified",
            "time": "not specified",
            "purpose": action_input,
        }

    # Step 2 — render the prompt with extracted values
    rendered = meeting_prompts.draft_email.render(
        recipient=fields["recipient"],
        date=fields["date"],
        time=fields["time"],
        purpose=fields["purpose"],
    )

    # Step 3 — call LLM with fully assembled prompt
    return extract_text(llm.invoke(rendered.to_prompt()))


def send_email_tool(content: str) -> str:
    return f"Email sent successfully with content:\n{content}"
