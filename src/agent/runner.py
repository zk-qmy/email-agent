# runner.py
import uuid
from langgraph.types import Command
from src.agent.state import initial_state
from src.agent.nodes.reasoning import extract_thought
from langchain_core.messages import HumanMessage, AIMessage


def is_asking_user(messages: list) -> bool:
    """In manual ReAct, agent asks a question when last message has no Action."""
    if not messages:
        return False
    last = str(messages[-1])
    # Agent replied with plain text thought but no Action → it's asking
    has_thought = last.startswith("Thought:")
    has_action = any(str(m).startswith("Action:") for m in messages[-2:])
    return "?" in last and not has_action


def run(app, user_message: str, thread_id: str = None) -> str:
    if thread_id is None:
        thread_id = str(uuid.uuid4())

    thread_config = {"configurable": {"thread_id": thread_id}}
    print(f"\nSession: {thread_id}")

    result = app.invoke(initial_state(user_message), config=thread_config)

    while True:
        snapshot = app.get_state(thread_config)
        messages = result.get("messages", [])

        # ── Case 1: waiting for tool approval ──────────────────────
        if snapshot.interrupts:
            interrupt_data = snapshot.interrupts[0].value
            print(f"\n⏸  {interrupt_data['question']}")
            user_input = input("Approve? (y/n) or type modified input: ").strip()

            if user_input.lower() == "y":
                resume = {"approved": True}
            elif user_input.lower() == "n":
                resume = {"approved": False}
            else:
                resume = {"approved": False, "action_input": user_input}

            result = app.invoke(Command(resume=resume), config=thread_config)

        # ── Case 2: LLM asked a question, needs user reply ──────────
        elif is_asking_user(messages):
            # Print the agent's question
            for m in reversed(messages):
                s = str(m)
                if s.startswith("Thought:") and "?" in s:
                    print(f"\nAssistant: {s.replace('Thought: ', '')}")
                    break

            user_input = input("You: ").strip()
            if not user_input:
                break

            # Append user reply and re-invoke
            result = app.invoke(
                {"messages": messages + [f"User: {user_input}"]},
                config=thread_config,
            )

        # ── Case 3: agent finished ───────────────────────────────────
        else:
            break

    print("\n=== Final Output ===")
    for msg in result.get("messages", []):
        thought = extract_thought(msg)
        if thought:
            print(f"Assistant: {thought}")

    return thread_id
