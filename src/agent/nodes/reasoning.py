# nodes/reasoning.py
from langchain_core.messages import SystemMessage, AIMessage
from src.integrations.llm.client import get_llm
from config.settings import settings
from src.agent.tools.registry import ALL_TOOLS

# Bind tools once — LLM now knows all schemas automatically
llm_with_tools = get_llm().bind_tools(ALL_TOOLS)

SYSTEM_PROMPT = """
                You are an email assistant.
                Use the available tools to complete the user's request.
                Always use the exact tool arguments — never guess or omit required fields.
                If you need more information from the user, ask clearly and wait for their response.
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
    iteration = state.get("iteration_count", 0)

    if iteration >= settings.MAX_ITERATIONS:
        return {
            "messages":    [AIMessage(content="Max iterations reached.")],
            "iteration_count": iteration,
        }

    response = llm_with_tools.invoke(
        [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    )

    # Print agent's thought
    thought = extract_thought(response)
    if thought:
        print(f"Thought: {thought}")

    if hasattr(response, "tool_calls") and response.tool_calls:
        for tc in response.tool_calls:
            print(f"Action:  {tc['name']}({tc['args']})")

    return {
        "messages":        [response],
        "iteration_count": iteration + 1,
    }
