import os
from src.integrations.llm.client import get_llm
from src.agent.utils import extract_text
from src.integrations.mail.sync_client import send_email_sync
from config.prompts.email import email_prompts

from typing import List
from langchain_core.tools import tool
from langgraph.types import interrupt

# Classification
# TODO: Classify department

# Summarization
# TODO: Add retrieve the email from database or conversation
@tool
def summarize_email(
    subject: str,
    body: str,
    sender: str,
    recipient: str
)-> str:
    """Summarize content in a email
    Args:
    
        subject: subject of the email
        body: email content
        sender: email's sender
        recipient: email's recipient
    """
    rendered = email_prompts.summarize_email.render(
        subject=subject,
        body=body,
        sender=sender,
        recipient=recipient
    )
    summarized_content = extract_text(get_llm().invoke(rendered.to_prompt()))
    return summarized_content

# Information Extraction
# TODO: Extract Meeting Info


# Check Missing Info

