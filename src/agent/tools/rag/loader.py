#src/agent/tools/rag/loader.py
import re
from dataclasses import dataclass
from src.agent.tools.rag.config import CHUNK_SIZE, OVERLAP

@dataclass
class Chunk:
    text: str
    section: str
    chunk_index: int


def load_markdown(md_path: str,
                  chunk_size=CHUNK_SIZE,
                  overlap=OVERLAP
                ) -> list[Chunk]:
    """Extract and chunk text from markdown file, tracking sections."""
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    chunks = []
    chunk_index = 0


    # Split by headings to preserve section context
    sections = re.split(r'(#{1,3} .+)', content)

    current_heading = "General"
    buffer = ""

    for part in sections:
        if re.match(r'#{1,3} .+', part):
            current_heading = part.strip()
            continue

        buffer += part

        # Chunk the buffer when it gets large enough
        while len(buffer) >= chunk_size:
            chunk_text = buffer[:chunk_size].strip()
            if chunk_text:
                chunks.append(Chunk(
                    text=chunk_text,
                    section=current_heading,
                    chunk_index=chunk_index
                ))
                chunk_index += 1
            buffer = buffer[chunk_size - overlap:]

    # Flush remaining buffer
    if buffer.strip():
        chunks.append(Chunk(
            text=buffer.strip(),
            section=current_heading,
            chunk_index=chunk_index
        ))

    return chunks