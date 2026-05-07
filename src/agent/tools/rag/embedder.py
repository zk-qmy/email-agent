# src/agent/tools/rag/embedder.py
import numpy as np
import faiss
import pickle
import os
from sentence_transformers import SentenceTransformer
from src.agent.tools.rag.loader import Chunk
from src.agent.tools.rag.config import MODEL_NAME, INDEX_CACHE_PATH


model = SentenceTransformer(MODEL_NAME)

def build_index(chunks: list[Chunk]):
    """Embed chunks and build FAISS index."""
    texts = [c.text for c in chunks]
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    return index, embeddings


def save_index(index, chunks: list[Chunk], path: str = INDEX_CACHE_PATH):
    """Save index to disk — avoid rebuilding every restart."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump({"index": index, "chunks": chunks}, f)
    print(f"Index saved to {path}")


def load_index(path: str = INDEX_CACHE_PATH):
    """Load index from disk."""
    with open(path, "rb") as f:
        data = pickle.load(f)
    return data["index"], data["chunks"]


def index_exists(path: str = INDEX_CACHE_PATH) -> bool:
    return os.path.exists(path)