from tests.rag.test_cases import TEST_CASES

import logging
from datetime import datetime
import os
from src.agent.tools.rag.retriever import retrieve
from src.agent.tools.rag.pipeline import get_index

# Create logs directory if not exists
os.makedirs("logs", exist_ok=True)

# Log file with timestamp
log_filename = f"logs/rag_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    encoding="utf-8"
)


def chunk_is_relevant(chunk_text: str, relevant_keywords: list[str]) -> bool:
    """Check if a chunk contains any of the relevant keywords."""
    chunk_lower = chunk_text.lower()
    return any(kw.lower() in chunk_lower for kw in relevant_keywords)


def recall_at_k(retrieved_chunks, relevant_keywords: list[str], k: int) -> float:
    """
    Recall@K = number of relevant keywords found in top K
    """
    top_k_chunks = retrieved_chunks[:k]

    keywords_found = set()

    for chunk in top_k_chunks:
        for kw in relevant_keywords:
            if kw.lower() in chunk.text.lower():
                keywords_found.add(kw.lower())

    if not relevant_keywords:
        return 0.0

    return len(keywords_found) / len(relevant_keywords)


def precision_at_k(retrieved_chunks, relevant_keywords: list[str], k: int) -> float:
    """
    Precision@K = relevant chunks in top K / K
    """
    top_k_chunks = retrieved_chunks[:k]

    relevant_count = sum(
        1 for chunk in top_k_chunks
        if chunk_is_relevant(chunk.text, relevant_keywords)
    )

    return relevant_count / k if k > 0 else 0.0


def log_result(message: str):
    #print(message)
    logging.info(message)


def evaluate(k_values: list[int] = [1, 3, 5]):
    index, chunks = get_index()

    log_result("=" * 60)
    log_result(f"RAG Evaluation — {len(TEST_CASES)} test cases")
    log_result("=" * 60)

    results = {k: {"recall": [], "precision": []} for k in k_values}

    for i, test in enumerate(TEST_CASES):
        query = test["query"]
        relevant_keywords = test["relevant_keywords"]

        max_k = max(k_values)

        retrieved = retrieve(
            query,
            index,
            chunks,
            top_k=max_k
        )

        log_result(f"\n[{i+1}] Query: {query}")
        log_result(f"Keywords: {relevant_keywords}")

        for k in k_values:
            recall = recall_at_k(retrieved, relevant_keywords, k)
            precision = precision_at_k(retrieved, relevant_keywords, k)

            results[k]["recall"].append(recall)
            results[k]["precision"].append(precision)

            log_result(
                f"@{k} → Recall: {recall:.2f} | Precision: {precision:.2f}"
            )

        log_result(f"Retrieved chunks (top {max_k}):")

        for j, chunk in enumerate(retrieved):
            relevant_marker = (
                "✓"
                if chunk_is_relevant(chunk.text, relevant_keywords)
                else "✗"
            )

            log_result(
                f"[{j+1}] {relevant_marker} "
                f"[{chunk.section}] "
                f"{chunk.text[:120]}..."
            )

    # Summary
    log_result("\n" + "=" * 60)
    log_result("SUMMARY")
    log_result("=" * 60)

    for k in k_values:
        avg_recall = (
            sum(results[k]["recall"])
            / len(results[k]["recall"])
        )

        avg_precision = (
            sum(results[k]["precision"])
            / len(results[k]["precision"])
        )

        log_result(f"Recall@{k}:    {avg_recall:.3f}")
        log_result(f"Precision@{k}: {avg_precision:.3f}")

    log_result(f"\nSaved evaluation log to: {log_filename}")

    return results


if __name__ == "__main__":
    evaluate(k_values=[1, 3, 5])