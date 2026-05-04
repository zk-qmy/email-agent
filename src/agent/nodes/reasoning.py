# nodes/reasoning.py
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from src.integrations.llm.client import get_llm
from src.agent.tools.registry import ALL_TOOLS
from langgraph.types import interrupt

# Bind tools once — LLM now knows all schemas automatically
llm_with_tools = get_llm().bind_tools(ALL_TOOLS)

system_prompt = """
You are an intelligent email assistant using a ReAct loop.

You must follow this format strictly:

Thought:
- Analyze the current situation
- Consider previous tool results (observations)

Action:
- If needed, call a tool with correct arguments
- If no tool is needed, respond directly to the user

Rules:
- Always reflect on the latest tool result before taking another action
- If a tool fails, DO NOT repeat the same action blindly
- If required information is missing, ask the user clearly
- Be precise with tool arguments — do not guess
- If draft_email tool is used, only call send_email tool after user approve the draft
from draft_email tool.
Draft email protocol:
- Call draft_email to generate and show a draft to the user
- If the result has "approved": false and "feedback" is non-empty:
  call draft_email AGAIN with previous_draft=<last draft> and user_feedback=<feedback>
- If the result has "approved": false and "feedback" is empty:
  the user cancelled — stop and confirm cancellation
- Only call send_email when "approved": true
- When calling send_email after an approved draft, always pass draft_approved=true

Email types:
- Use email_type='meeting' when user wants to schedule a meeting — requires date and time
- Use email_type='general' for all other emails — use key_points to capture what to say

Important:
- When calling send_general_email or send_meeting_email, use user_id='default_user' if not provided
- Extract recipient email from the conversation if mentioned, otherwise ask ONCE and remember the answer
- Never ask for the same information twice

You will receive tool results as observations in the conversation.

Your goal is to iteratively act, observe, and improve until the task is complete.
"""


def extract_thought(response) -> str:
    """Extract only the text content from an AIMessage."""
    content = response.content

    # Already a plain string
    if isinstance(content, str):
        return content.strip()

    # List of blocks — grab only text blocks
    if isinstance(content, list):
        return " ".join(
            block["text"]
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ).strip()

    return ""


def reasoning_node(state):
    messages = state["messages"]

    if messages and isinstance(messages[-1], ToolMessage):
        last_tool_msg = messages[-1]
        print(f"=== Observation: {last_tool_msg.content} ===\n")
        messages = messages + [
            SystemMessage(
                content=f"""
                Observation:
                  {last_tool_msg.content}

                Reflection:
                - Was this successful?
                - If not, what should be corrected?
                - What is the next best action?
                Do NOT jump to another tool without reasoning.
                """
            )
        ]

    response = llm_with_tools.invoke([SystemMessage(content=system_prompt)] + messages)
    # print(f"=== Reasoning raw response: {response}\n")

    thought = extract_thought(response)
    if thought:
        print(f"=== Thought: {thought} ===\n")

    if not getattr(response, "tool_calls", None):
        print("=== Reasoning Node: Getting user input...")
        user_input = interrupt({"question": thought})
        user_content = (
            user_input
            if isinstance(user_input, str)
            else user_input.get("input") or user_input.get("response") or ""
        )
        return {
            "messages": [
                response,
                HumanMessage(content=user_content),
            ]
        }

    for tc in response.tool_calls:
        print(f"Action:  {tc['name']}({tc['args']})")

    return {"messages": [response]}
