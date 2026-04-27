import json
from src.integrations.llm.client import get_llm
from config.settings import settings
from src.agent.tools.registry import TOOL_DESCRIPTIONS
from src.agent.utils import extract_text
import json
import re


def parse_llm_json(text: str) -> dict:
    # Strip ```json ... ``` or ``` ... ``` fences
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text.strip())

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try extracting the first {...} block as a fallback
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

    return {"thought": "parse failed", "action": "final", "action_input": text}


def build_prompt(history: str) -> str:
    return f"""
            You are an email assistant using ReAct reasoning.

            Available tools:
            {TOOL_DESCRIPTIONS}

            Format STRICTLY in JSON:Respond with ONLY a raw JSON object
            — no markdown, no code fences, no explanation.
            {{
            \"thought\": \"what you think\",
            \"action\": \"tool name OR final\",
            \"action_input\": \"input for tool OR final answer\"
            }}

            Conversation:
            {history}
            """


def reasoning_node(state):
    iteration = state.get("iteration_count", 0)
    if iteration >= settings.MAX_ITERATIONS:
        return {"messages": ["Final: Max iterations reached."], "next_action": "final"}

    response = get_llm().invoke(build_prompt("\n".join(state["messages"])))
    text = extract_text(response)

    try:
        decision = parse_llm_json(text)
    except json.JSONDecodeError:
        decision = {"thought": "fallback", "action": "final", "action_input": text}

    print(f"Thought: {decision['thought']}")
    print(f"Action:  {decision['action']}")
    return {
        "messages": [
            f"Thought: {decision['thought']}",
            f"Action: {decision['action']}({decision['action_input']})",
        ],
        "thought": decision["thought"],
        "action": decision["action"],
        "action_input": decision["action_input"],
        "next_action": decision["action"],
        "iteration_count": iteration,
    }
