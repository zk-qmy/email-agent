from config.prompts.scheduling import meeting_prompts

if __name__ == "__main__":
    prompt = meeting_prompts.get("extract_meeting_info")
    print(prompt.system.template)
