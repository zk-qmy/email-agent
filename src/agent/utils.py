# utils.py
def extract_text(response) -> str:
    '''
    Extract plain text from LLM responses,
    regardless of content format'''
    content = response.content
    if isinstance(content, list):
        return " ".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        ).strip()
    return content.strip()
