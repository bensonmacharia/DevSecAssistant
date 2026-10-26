from pathlib import Path

from src.devsecassistant.chunking import chunk_records
from src.devsecassistant.ingestion import ingest_directory
from src.devsecassistant.retrieval import (
    DEFAULT_MODEL,
    SemanticRetriever,
)


def build_index(
    directory: str | Path,
    chunk_size: int = 1000,
    overlap: int = 150,
    model_name: str = DEFAULT_MODEL,
) -> SemanticRetriever:
    """Ingest documents, chunk their text, and build a semantic index."""

    source_directory = Path(directory)

    if not source_directory.is_dir():
        raise NotADirectoryError(
            f"Document directory does not exist: {source_directory}"
        )

    records = ingest_directory(source_directory)

    if not records:
        raise ValueError(f"No supported documents found in: {source_directory}")

    chunks = chunk_records(
        records,
        chunk_size=chunk_size,
        overlap=overlap,
    )

    if not chunks:
        raise ValueError(f"No text could be extracted from: {source_directory}")

    retriever = SemanticRetriever(model_name=model_name)
    retriever.index(chunks)

    return retriever
