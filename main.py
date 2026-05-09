from src.agent.graph import build_graph, save_graph
import os
from src.agent.runner import run
import asyncio


print(os.getcwd())
print(__file__)

if __name__ == "__main__":
    app = build_graph()
    # save_graph(app)
    initial_prompt = "help me write an email to prof linh to schedule a meeting on 2nd may"
    asyncio.run(run(app, initial_prompt))
