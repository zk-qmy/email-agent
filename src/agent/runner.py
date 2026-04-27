import uuid
from langgraph.types import Command
from src.agent.state import initial_state


def run(app, user_message: str, thread_id: str = None) -> str:
    if thread_id is None:
        thread_id = str(uuid.uuid4())  # unique per session

    thread_config = {"configurable": {"thread_id": thread_id}}
    print(f"\nSession: {thread_id}")

    result = app.invoke(initial_state(user_message), config=thread_config)

    while True:
        snapshot = app.get_state(thread_config)
        if not snapshot.interrupts:
            break

        interrupt_data = snapshot.interrupts[0].value
        print(f"\n\u23f8  {interrupt_data['question']}")
        user_input = input("Approve? (y/n) or type modified input: ").strip()

        if user_input.lower() == "y":
            resume = {"approved": True}
        elif user_input.lower() == "n":
            resume = {"approved": False}
        else:
            resume = {"approved": True, "action_input": user_input}

        result = app.invoke(Command(resume=resume), config=thread_config)

    print("\n=== Final Output ===")
    for msg in result["messages"]:
        print(msg)

    return thread_id
