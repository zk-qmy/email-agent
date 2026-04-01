import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from langgraph.types import Command
from langchain_core.runnables.config import RunnableConfig
from src.core.states import AgentState, EmailData
from src.workflows.router import build_router


def run():
    graph = build_router()
    initial_state = AgentState(
        messages=[
            {
                "role": "user",
                "content": "Schedule a meeting with Prof Linh next Monday at 12 am",
            }
        ],
        email=EmailData(),
    )
    config: RunnableConfig = {
        "configurable": {"thread_id": "session-1", "user_id": 1},
        "recursion_limit": 25,
    }

    result = graph.invoke(initial_state, config=config)

    while "__interrupt__" in result:
        print("\n--- INTERRUPTED ---")
        interrupt_data = result["__interrupt__"][0].value
        print("Message:", interrupt_data.get("message", ""))

        if "email_draft" in interrupt_data:
            print("\nDraft Email:\n", interrupt_data["email_draft"])
            prompt = "Type: approved / edit / cancel: "
        else:
            prompt = "Your reply: "

        user_input = str(input(prompt))
        result = graph.invoke(
            Command(resume={"role": "user", "content": user_input}),
            config=config,
        )
        print("\nResult:", result)


if __name__ == "__main__":
    run()
