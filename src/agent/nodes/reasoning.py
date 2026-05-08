# nodes/reasoning.py
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from src.integrations.llm.client import get_llm
from src.agent.tools.registry import ALL_TOOLS
from config.reasoning_prompts.reasoning import REASONING_PROMPT2
from langgraph.types import interrupt

# Bind tools once — LLM now knows all schemas automatically
llm_with_tools = get_llm().bind_tools(ALL_TOOLS)
reasoning_prompt = REASONING_PROMPT2

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

    response = llm_with_tools.invoke([SystemMessage(content=reasoning_prompt)] + messages)
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
