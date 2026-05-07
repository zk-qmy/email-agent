import base64
from src.integrations.llm.client import get_llm
from src.agent.utils import extract_text
from config.prompts.files import file_prompts
from config.prompts.email import email_prompts
from src.integrations.mail.sync_client import get_email_by_index_sync
import json
import pdfplumber
from langchain_core.tools import tool
from langgraph.types import interrupt

# === CLASSIFICATION ===
# TODO: Classify department

# === SUMMARIZATION ===
# Placeholder
@tool
def get_email_content_test(user_id: int, index: int = 0) -> dict:
    """get the email content of current user

    Args:
        user_id (int): current user id
        index (int, optional): The order of the email in the inbox

    Returns:
        dict: a dictionary of information of the email
    """
    try:
        email = get_email_by_index_sync(user_id, index)
        print(json.dumps(email, indent=2))
        return {
            "status": "success",
            "source": "live_backend",
            "subject": email["subject"],
            "body": email["body"],
            "sender": email["sender_email"],
            "recipient": email["recipient_email"],
        }
    except ValueError as e:
        return {"status": "error", "error": str(e)}
    except Exception as e:
        return {"status": "error", "error": f"Failed to get email: {e}"}

@tool
def summarize_email(
    # email_id: int,
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

# === Information Extraction ===
# TODO: Extract Meeting Info


# === CHECK MISSING PDF INFO ===
@tool
def parse_pdf(file_path: str)-> str:
    '''
    Extract text content from raw PDF file
    
    Args:
        file_path (str): path to local PDF file
    Returns:
        str: file's content
    '''
    try:
        with pdfplumber.open(file_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + '\n'
        result = " ".join(full_text.split())
        return result
    except FileNotFoundError:
        return f"File not found: {file_path}"
    except Exception as e:
        return f"Error: {str(e)}"
    

@tool
def validate_pdf(file_content: str, user_role: str) -> dict:
    """Check if there are missing fields that user should fill in

    Args:
        file_content (str): extracted content from raw PDF
        user_role (str): role of current user

    Returns:
        dict: _description_
    """
    rendered = file_prompts.check_pdf_form_completion.render(
        text=file_content,
        role=user_role
    )
    validate_result_text = extract_text(get_llm().invoke(rendered.to_prompt()))
    try:
        result = json.loads(validate_result_text)
    except json.JSONDecodeError:
        result = {
            "error": "Invalid JSON output from LLM",
            "raw_output": validate_result_text
        }
    return result
    
