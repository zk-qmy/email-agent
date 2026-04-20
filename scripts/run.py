from src.workflows.registry import startup
from contextlib import asynccontextmanager
from fastapi import FastAPI

from config.prompts.registry import get_prompts
from src.core.state_registry import get_state_schema
from src.workflows.registry import classify_workflow
from src.workflows.registry import get_graph
from src.workflows.registry import startup
from langchain_core.runnables.config import RunnableConfig
from langgraph.types import Command
from src.workflows.ticket.state import EmailData
import sys
import os


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     startup()   # compile graphs once, cleanly
#     yield

# app = FastAPI(lifespan=lifespan)

def run():
    #user_input = "Book a meeting with Prof Linh next Monday at 12 am"
    user_input = (
        "I need to submit an Academic Accommodation request. "
        "My name is Nguyen Van A, student ID 220123. "
        "My GPA is 3.2 and I have completed 65 credits. "
        "I need the accommodation due to a medical condition diagnosed this semester. "
        "My advisor email is advisor.tran@student.fulbright.eud.vn and "
        "registrar email is registrar@fulbright.edu.vn"
        )
    workflow_name = classify_workflow(user_input)
    print(f"Classified workflow: {workflow_name}")

    graph = get_graph(workflow_name)

    # TODO: get_state_schema return a string not a class, need to fix that
    StateClass = get_state_schema(workflow_name)

    initial_state = StateClass(
        messages=[
            {
                "role": "user",
                "content": user_input,
            }
        ],
        #email=EmailData(),
    )
    '''
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
    }
    '''
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
    startup()  # compile graphs once, cleanly
    run()
