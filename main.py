from src.agent.graph import build_graph, save_graph
import os
from src.agent.runner import run
import subprocess

print(os.getcwd())
print(__file__)

if __name__ == "__main__":
    app = build_graph()
    # save_graph(app)
    # Test summarize email
    #initial_prompt = "summarize this email: Hi Bob,\n\nI wanted to give you a quick update on the recommendation system project. We have completed the data preprocessing and initial model training, and the results look promising so far.\n\nHowever, we still need to fine-tune the model and run additional evaluations before finalizing the results. Could you please review the current progress and share your feedback by Friday?\n\nAlso, let me know if you're available for a short meeting next Monday to discuss the next steps.\n\nBest regards,\nAlice"
    
    # Test summarize current email
    #initial_prompt = "help me summarize current email, my current user id is 1"
    #run(app, initial_prompt)
    
    # Test draft + send email
    #initial_prompt = "help me write an email to prof linh to schedule a meeting on 2nd may"
    #run(app, initial_prompt)
    
    # PDF valiadation
    #initial_prompt = "check this pdf if there is still something missing"
    #pdf_path = r'D:\email-agent\test-pdf\Maximum-Course-Load-Request.pdf'
    #run(app, initial_prompt, pdf_path)
    
    # Test suggest department with RAG
    initial_prompt = "I want to change my room who should i contact"
    run(app, initial_prompt)
    
    # Test ask guide with RAG
    # initial_prompt = ""
    # run(app, initial_prompt)
