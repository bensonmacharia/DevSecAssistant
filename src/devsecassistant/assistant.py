from pathlib import Path
from typing import Any

from src.devsecassistant.generation import generate_answer
from src.devsecassistant.pipeline import build_index
from src.devsecassistant.retrieval import DEFAULT_MODEL, SemanticRetriever


ABSTENTION_MESSAGE = "I don't have an answer for that."


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
                "answer": ABSTENTION_MESSAGE,
                "sources": [],
                "abstained": True,
                "retrieved_count": len(passages),
                "used_evidence_count": 0,
                "citation_valid": None,
                "citation_errors": [],
            }

        result = generate_answer(
            question,
            relevant_passages,
            model_name=self.llm_model,
        )

        result["abstained"] = result.get("abstained", False)
        result["retrieved_count"] = len(passages)
        result["used_evidence_count"] = len(relevant_passages)

        if result["abstained"]:
            result["answer"] = ABSTENTION_MESSAGE
            result["sources"] = []
            result["citation_valid"] = None
            result["citation_errors"] = []

        return result
