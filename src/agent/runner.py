# runner.py
import uuid
from langgraph.types import Command
from src.agent.state import initial_state
from src.agent.nodes.reasoning import extract_thought
from langchain_core.messages import HumanMessage


def is_asking_user(messages: list) -> bool:
    """In manual ReAct, agent asks a question when last message has no Action."""
    if not messages:
        return False
    last = str(messages[-1])
    # Agent replied with plain text thought but no Action → it's asking
    # has_thought = last.startswith("Thought:")
    has_action = any(str(m).startswith("Action:") for m in messages[-2:])
    return "?" in last and not has_action


def run(app, user_message: str, thread_id: str = None) -> str:
    if thread_id is None:
        thread_id = str(uuid.uuid4())

    thread_config = {"configurable": {"thread_id": thread_id}}
    print(f"\nSession: {thread_id}")

    result = app.invoke(initial_state(user_message), config=thread_config)

    # ── Keep handling interrupts until graph is done ──────────────
    while True:
        snapshot = app.get_state(thread_config)

        if not snapshot.interrupts:
            break  # graph finished, no more interrupts

        interrupt_data = snapshot.interrupts[0].value
        interrupt_type = interrupt_data.get("type", "")
        print(f"\n⏸  {interrupt_data['question']}")

        if interrupt_type == "review_draft":
            user_input = input("Approve? (y/n) or type modified input: ").strip()
            # Handle approval
            if user_input.lower() == "y":
                resume = {"approved": True}
            elif user_input.lower() == "n":
                resume = {"approved": False}
                break
            else:
                resume = {"approved": False, "action_input": user_input}

            result = app.invoke(Command(resume=resume), config=thread_config)

        elif interrupt_type == "confirm_send":
            user_input = input("Send? (y/n): ").strip()
            if user_input.lower() == "y":
                result = app.invoke(
                    Command(resume={"approved": True}), config=thread_config
                )
            elif user_input.lower() == "n":
                resume = {"approved": False}
                break  # stop loop if not approved
            else:
                resume = {"approved": False, "action_input": user_input}
                result = app.invoke(
                    Command(resume=resume),
                    config=thread_config
                )
        else:
            # fallback for unknown interrupt types
            user_input = input("Your input: ").strip()
            app.update_state(
                thread_config,
                {"messages": [HumanMessage(content=user_input)]},
            )
            result = app.invoke(
                Command(resume=user_input),
                config=thread_config
            )

        # result = app.invoke(Command(resume=resume), config=thread_config)
    # ── LLM asked a question ──────────────────────────────────────
    if result is None:  # guard against None result
        return thread_id
    # ── Case 2: LLM asked a question ─────────────────────────────
    messages = result.get("messages", [])
    if is_asking_user(messages):
        for m in reversed(messages):
            s = str(m)
            if s.startswith("Thought:") and "?" in s:
                print(f"\nAssistant: {s.replace('Thought: ', '')}")
                break

        user_input = input("You: ").strip()
        if user_input:
            result = app.invoke(
                {"messages": messages + [f"User: {user_input}"]},
                config=thread_config,
            )

    # ── Final output ──────────────────────────────────────────────
    print("\n=== Final Output ===")
    for msg in result.get("messages", []):
        thought = extract_thought(msg)
        if thought:
            print(f"Assistant: {thought}")

    return thread_id
