from src.agent.graph import build_graph, save_graph
import os
from src.agent.runner import run


print(os.getcwd())
print(__file__)

if __name__ == "__main__":
    app = build_graph()
    # save_graph(app)
    initial_prompt = "write an email to schedule a meeting with prof Linh (li@gmal.com) to discuss above a project tomorrow (31/04/2026 at 2pm) and send it to him."
    run(app, initial_prompt)
