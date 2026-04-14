import argparse
from datetime import datetime
from src.workflows.router import build_router
from src.core.states import AgentState, EmailData
from langchain_core.runnables.config import RunnableConfig
from langgraph.types import Command
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def run(args):
    graph = build_router()

    if args.graph_only:
        filename = datetime.now().strftime("meeting_graph_%Y%m%d_%H%M%S.png")
        os.makedirs("assets/graph", exist_ok=True)
        png_data = graph.get_graph(xray=True).draw_mermaid_png()
        with open(f"assets/graph/{filename}", "wb") as f:
            f.write(png_data)
        print(f"Saved to assets/graph/{filename}")
        return

    user_input = (
        args.message or "Schedule a meeting with Prof Linh next Monday at 12 am"
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
        "configurable": {
            "thread_id": "session-1",
            "user_id": 1,
            "mock_reply": args.simulate_reply,
            "fallback_to_queue": args.no_backend,
            "no_response_count": args.no_response_count,
        },
        "recursion_limit": 50,
    }

    result = graph.invoke(initial_state, config=config)

    while "__interrupt__" in result:
        print("\n--- INTERRUPTED ---")
        interrupt_data = result["__interrupt__"][0].value
        print("Message:", interrupt_data.get("message", ""))

        if "email_draft" in interrupt_data:
            print("\nDraft Email:\n", interrupt_data.get("email_draft", ""))
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
    parser = argparse.ArgumentParser(description="Email Agent Runner")
    parser.add_argument(
        "--no-backend",
        action="store_true",
        help="Simulate no backend - emails skipped (soft fail)",
    )
    parser.add_argument(
        "--simulate-reply",
        choices=["confirmed", "negotiate", "declined"],
        help="Simulate reply from recipient",
    )
    parser.add_argument(
        "--max-followups",
        type=int,
        default=2,
        help="Max follow-up attempts before giving up",
    )
    parser.add_argument(
        "--no-response-count",
        type=int,
        default=0,
        help="Simulate N rounds of no reply before ending flow",
    )
    parser.add_argument("-m", "--message", type=str, help="Initial user message")
    parser.add_argument(
        "--graph-only",
        action="store_true",
        help="Only generate graph PNG, don't run workflow",
    )
    args = parser.parse_args()
    run(args)
