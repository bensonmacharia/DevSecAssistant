from pathlib import Path

import pytest

from src.devsecassistant.pipeline import build_index

FIXTURES = Path("tests/fixtures")


def test_pipeline_retrieves_password_policy():
    retriever = build_index(FIXTURES)

    results = retriever.search(
        "What are the password requirements for external portals?",
        top_k=3,
    )

    assert results
    assert any("password" in result["text"].lower() for result in results)

    assert all("source_file" in result for result in results)
    assert all("location" in result for result in results)
    assert all("score" in result for result in results)


def test_pipeline_rejects_missing_directory(tmp_path):
    missing_directory = tmp_path / "does-not-exist"

    with pytest.raises(NotADirectoryError):
        build_index(missing_directory)


def test_pipeline_rejects_directory_without_documents(tmp_path):
    with pytest.raises(ValueError, match="No supported documents"):
        build_index(tmp_path)
