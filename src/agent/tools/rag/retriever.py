# src/agent/tools/rag/retriever.py
import numpy as np
from sentence_transformers import SentenceTransformer
from src.agent.tools.rag.loader import Chunk
from src.agent.tools.rag.config import MODEL_NAME

model = SentenceTransformer(MODEL_NAME)

def retrieve(query: str, index, chunks: list[Chunk], top_k: int = 3) -> list[Chunk]:
    """Find most relevant chunks for a query."""
    query_embedding = model.encode([query], convert_to_numpy=True)
    query_embedding = query_embedding / np.linalg.norm(query_embedding)

    scores, indices = index.search(query_embedding, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < len(chunks):
            chunk = chunks[idx]
            # Changed from chunk.page to chunk.section
            print(f"  [RAG] section={chunk.section} score={score:.3f} → {chunk.text[:80]}...")
            results.append(chunk)
    print(f"Original RAG result from retrive(): {results}")
    return results