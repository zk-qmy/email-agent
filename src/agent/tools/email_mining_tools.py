import base64
from src.integrations.llm.client import get_llm
from src.agent.utils import extract_text
from config.tool_prompts.files import file_prompts
from config.tool_prompts.email import email_prompts
from config.tool_prompts.rag import rag_prompts
from src.integrations.mail.sync_client import get_email_by_index_sync, get_thread_emails_sync, get_threads_sync
import json
import pdfplumber
from langchain_core.tools import tool
from langgraph.types import interrupt
from src.agent.tools.rag.pipeline import query_guide

# === CLASSIFICATION ===
@tool
def suggest_department(student_request: str) -> dict:
    """suggest department to send to base on student_request

    Args:
        student_request (str): request from student
    """
    try:
        context = query_guide(student_request)
        rendered = rag_prompts.suggest_department.render(
            context=context,
            student_request=student_request
        )
        result = extract_text(get_llm().invoke(rendered.to_prompt()))
        print(f'raw suggest_department llm response: {result}')
        clean = result.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        print(f"clean version: {clean}")
        return json.loads(clean)
    except Exception as e:
        return {"error": str(e)}

# === GENERAL RAG
@tool
def ask_guide(question: str) -> dict:
    """retrieve information from document using RAG

    Args:
        question (str): user's question

    Returns:
        dict: _description_
    """
    try:
        context = query_guide(question)
        rendered = rag_prompts.ask_guide.render(
            context=context,
            question=question
        )
        result = extract_text(get_llm().invoke(rendered.to_prompt()))
        clean = result.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(clean)
    except Exception as e:
        return {"error:": str(e)}
    
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

# === THREAD MANAGEMENT ===
@tool
def list_email_threads(user_id: int) -> str:
    """List all email threads for the current user with their thread IDs and subjects.

    Args:
        user_id (int): current user id
    """
    try:
        resp = get_threads_sync(user_id)
        threads = resp.get("threads", [])
        if not threads:
            return "No threads found."
        lines = ["Email Threads:"]
        for t in threads:
            lines.append(
                f"  - Thread ID: {t['thread_id']} | Subject: {t['subject']} "
                f"| Emails: {t['email_count']} | Last: {t['last_email_at']}"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"Failed to list threads: {e}"


@tool
def get_thread_content(user_id: int, thread_id: str) -> dict:
    """Fetch all emails in a thread by thread ID so the LLM can inspect them.

    Args:
        user_id (int): current user id
        thread_id (str): the thread ID to fetch
    """
    try:
        resp = get_thread_emails_sync(thread_id, user_id)
        emails = resp if isinstance(resp, list) else resp.get("emails", [])
        return {
            "status": "success",
            "thread_id": thread_id,
            "email_count": len(emails),
            "emails": emails,
        }
    except Exception as e:
        return {"status": "error", "error": f"Failed to get thread: {e}"}


# === SUMMARIZATION ===
@tool
def summarize_email(user_id: int, thread_id: str) -> str:
    """Summarize an entire email thread by its thread ID.
    Fetches all emails in the thread and provides a structured summary.

    Args:
        user_id (int): current user id
        thread_id (str): the thread ID of the email thread to summarize
    """
    try:
        resp = get_thread_emails_sync(thread_id, user_id)
        emails = resp if isinstance(resp, list) else resp.get("emails", [])
        if not emails:
            return "No emails found in this thread."

        subject = emails[0].get("subject", "(no subject)")
        email_lines = []
        for i, e in enumerate(emails, 1):
            sender = e.get("sender_email", "unknown")
            recipient = e.get("recipient_email", "unknown")
            body = (e.get("body") or "").strip()
            short_body = body[:500] + "..." if len(body) > 500 else body
            email_lines.append(
                f"  [{i}] From: {sender}  To: {recipient}\n"
                f"      Date: {e.get('created_at', '')}\n"
                f"      Body: {short_body}"
            )

        email_list_str = "\n".join(email_lines)
        rendered = email_prompts.summarize_email.render(
            subject=subject,
            email_list=email_list_str,
        )
        summarized_content = extract_text(get_llm().invoke(rendered.to_prompt()))
        return summarized_content
    except Exception as e:
        return f"Failed to summarize thread: {e}"

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
    
