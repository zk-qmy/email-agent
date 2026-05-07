# src/agent/tools/rag/pipeline.py
from functools import lru_cache
from src.agent.tools.rag.loader import load_markdown, Chunk
from src.agent.tools.rag.embedder import build_index, save_index, load_index, index_exists
from src.agent.tools.rag.retriever import retrieve
from functools import lru_cache
from src.agent.tools.rag.config import INDEX_CACHE_PATH, DEPARTMENT_MD_PATH
import os

@lru_cache(maxsize=1)
def get_index():
    """Load from cache if exists, otherwise build from MD."""
    if index_exists():
        print("[RAG] Loading index from cache...")
        try:
            index, chunks = load_index()
            # Verify if chunks have the 'section' attribute, if not, force rebuild
            # This handles cases where old cached data (with 'page' attribute) is present
            if not chunks or not hasattr(chunks[0], 'section'):
                raise ValueError("Cached chunks do not have 'section' attribute or are empty. Rebuilding index.")
            return index, chunks
        except Exception as e:
            print(f"[RAG] Error loading cached index ({e}). Rebuilding...")
            # Remove old cache to force rebuild
            if os.path.exists(INDEX_CACHE_PATH):
                os.remove(INDEX_CACHE_PATH)
            return _build_new_index()
    else:
        print("[RAG] Building index from MD...")
        return _build_new_index()

def _build_new_index():
    # Use load_markdown as DEPARTMENT_MD_PATH points to a markdown file
    chunks = load_markdown(DEPARTMENT_MD_PATH)
    index, _ = build_index(chunks)
    save_index(index, chunks)
    return index, chunks

def query_guide(question: str, top_k: int = 3) -> str:
    """Main entry point — returns relevant context as a string."""
    index, chunks = get_index()
    relevant_chunks = retrieve(question, index, chunks, top_k)

    # Format for LLM prompt, using chunk.section
    context = ""
    for chunk in relevant_chunks:
        context += f"[Section: {chunk.section}]\n{chunk.text}\n\n"

    return context.strip()