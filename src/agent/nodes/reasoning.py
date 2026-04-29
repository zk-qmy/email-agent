# nodes/reasoning.py
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from src.integrations.llm.client import get_llm
from src.agent.tools.email_tools import ALL_TOOLS
from langgraph.types import interrupt

# Bind tools once — LLM now knows all schemas automatically
llm_with_tools = get_llm().bind_tools(ALL_TOOLS)

extra_prompt = """
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
    # ReAct system prompt
    messages = state["messages"]  # get user messages, AI responses, tool outputs

    draft_injection = ""
    if state.get("draft_approved") and state.get("approved_draft"):
        draft_injection = (
            "The user has already approved this email draft. "
            "Do NOT call draft_email again. Call send_email directly with this content:\n\n"
            + state["approved_draft"]
        )

    if messages and isinstance(
        messages[-1], ToolMessage
    ):  # get Observation + Reflection
        last_tool_msg = messages[-1]
        print(f"Observation: {last_tool_msg.content}")
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

    response = llm_with_tools.invoke([SystemMessage(content=draft_injection)] + messages)

    # Print agent's thought
    thought = extract_thought(response)
    if thought:
        print(f"Thought: {thought}")

    # HIL
    if not getattr(response, "tool_calls", None):
        print("Reasoning Node: Getting user input...")
        # Ask user
        user_input = interrupt({"question": thought})
        print(f"Reasoning Node - user_input: {user_input}")

        return {
            "messages": [
                response,
                HumanMessage(  # inject user reply
                    content=(
                        user_input
                        if isinstance(user_input, str)
                        else user_input.get("input", "")
                    )
                ),
            ]
        }
    # Call tools
    if hasattr(response, "tool_calls") and response.tool_calls:
        print("Reasoning node: calling tools")
        for tc in response.tool_calls:
            print(f"Action:  {tc['name']}({tc['args']})")

    return {
        "messages": [response],
    }
