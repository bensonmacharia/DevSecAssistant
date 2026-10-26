from pathlib import Path
from typing import Any

from src.devsecassistant.generation import generate_answer
from src.devsecassistant.pipeline import build_index
from src.devsecassistant.retrieval import DEFAULT_MODEL, SemanticRetriever


class DevSecAssistant:
    """Question-answering assistant grounded in indexed documents."""

    def __init__(
        self,
        document_directory: str | Path,
        embedding_model: str = DEFAULT_MODEL,
        llm_model: str = "qwen2.5-coder:7b",
        min_similarity: float = 0.35,
    ) -> None:
        if not -1.0 <= min_similarity <= 1.0:
            raise ValueError("min_similarity must be between -1 and 1")

        self.llm_model = llm_model
        self.min_similarity = min_similarity
        self.retriever: SemanticRetriever = build_index(
            document_directory,
            model_name=embedding_model,
        )

    def ask(
        self,
        question: str,
        top_k: int = 3,
    ) -> dict[str, Any]:
        """Answer a question using sufficiently similar passages."""

        if not question.strip():
            raise ValueError("question must not be empty")

        passages = self.retriever.search(question, top_k=top_k)

        # Initial relevance gate. Its threshold must be calibrated
        # against a representative evaluation dataset.
        relevant_passages = [
            passage for passage in passages if passage["score"] >= self.min_similarity
        ]

        if not relevant_passages:
            return {
                "answer": (
                    "I could not find sufficiently relevant evidence "
                    "in the indexed documents to answer this question."
                ),
                "sources": [],
                "abstained": True,
                "retrieved_count": len(passages),
            }

        result = generate_answer(
            question,
            relevant_passages,
            model_name=self.llm_model,
        )

        result["abstained"] = False
        result["retrieved_count"] = len(passages)
        result["used_evidence_count"] = len(relevant_passages)

        return result
