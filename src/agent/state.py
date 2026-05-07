# state.py
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph.message import add_messages
import base64

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    draft_approved: bool


def _load_pdf_as_base64(file_path: str) -> str:
    try:
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print(f"Error loading PDF path: {e}")

def initial_state(user_message: str, pdf_path: str = None) -> AgentState:
    content = [{"type": "text", "text": user_message}]

    if pdf_path:
        pdf_b64 = _load_pdf_as_base64(pdf_path)
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:application/pdf;base64,{pdf_b64}"
            }
        })

    return {
        "messages": [HumanMessage(content=content)],
    }
