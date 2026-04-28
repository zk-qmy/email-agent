from src.agent.graph import build_graph, save_graph
from src.agent.runner import run
import os
#import sys

print(os.getcwd())  # current working directory
print(__file__)  # path to the current file
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
if __name__ == "__main__":
    app = build_graph()  # one compiled graph, shared across sessions
    # save_graph(app)
    run(app, "write an email to schedule a meeting with prof Linh tommorrow and sent to him.")
