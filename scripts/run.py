from datetime import datetime
from src.workflows.router import build_router
from src.core.states import AgentState, EmailData
from langchain_core.runnables.config import RunnableConfig
from langgraph.types import Command
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def run():
    graph = build_router()
    # Print Image
    filename = datetime.now().strftime(
        "meeting_graph_%Y%m%d_%H%M%S.png")

    os.makedirs("assets/graph", exist_ok=True)
    png_data = graph.get_graph(xray=True).draw_mermaid_png()
    with open(f"assets/graph/{filename}", "wb") as f:
        f.write(png_data)
    print(f"Saved to assets/graph/{filename}")

    # Run the graph with an initial user message
    user_input = (
        """
        "Schedule a meeting with Prof Linh next Monday at 12 am."
        "I want to discuss with him about the review content for the next exam."
        "Write the email 20 sentences long"
        """
        )
    initial_state = AgentState(
        messages=[
            {
                "role": "user",
                "content": user_input,
            }
        ],
        email=EmailData(),
    )
    config: RunnableConfig = {
        "configurable": {"thread_id": "session-1", "user_id": 1},
        "recursion_limit": 25,
    }

    # continue

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
        print("\nAfter Resume:", result)


if __name__ == "__main__":
    run()
