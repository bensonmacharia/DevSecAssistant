from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class SemanticRetriever:
    """Retrieve relevant document chunks using embedding similarity."""

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
    ) -> None:
        self.model = SentenceTransformer(model_name)
        self.chunks: list[dict[str, Any]] = []
        self.embeddings: np.ndarray | None = None

    def index(self, chunks: list[dict[str, Any]]) -> None:
        """Create embeddings for document chunks."""
        self.chunks = list(chunks)

        if not self.chunks:
            self.embeddings = np.empty((0, 0), dtype=np.float32)
            return

        texts = [chunk["text"] for chunk in self.chunks]

        self.embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

    def search(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[dict[str, Any]]:
        """Return the most relevant chunks for a query."""
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        if not query.strip():
            raise ValueError("query must not be empty")

        if self.embeddings is None:
            raise RuntimeError("Index documents before searching")

        if not self.chunks:
            return []

        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )[0]

        # Normalized embeddings allow dot product to represent
        # cosine similarity.
        scores = self.embeddings @ query_embedding

        # Stable ordering: highest similarity first.
        ranked_indices = np.argsort(-scores, kind="stable")[:top_k]

        results = []
        for index in ranked_indices:
            result = dict(self.chunks[int(index)])
            result["score"] = float(scores[index])
            results.append(result)

        return results
