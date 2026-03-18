from typing import Literal
from pydantic import BaseModel
from src.core.states import AgentState
from src.integrations.llm.client import get_llm


class WorkflowOutput(BaseModel):
    workflow: Literal["schedule", "ticket", "chat"]


def classify_workflow(state: AgentState) -> dict:
    user_input = state.messages[-1]["content"]
    structured_llm = get_llm().with_structured_output(WorkflowOutput)
    response = structured_llm.invoke([
        {
            "role": "system",
            "content": (
                "Classify the user's request into exactly one of:\n"
                "- schedule (meeting scheduling)\n"
                "- ticket (support or issue ticket)\n"
                "- chat (general conversation)\n\n"
                "If uncertain, choose the closest match. Return only structured output."
            ),
        },
        {"role": "user", "content": user_input},
    ])
    print(f"[classify] workflow: {response.workflow}")
    return {"workflow": response.workflow}
