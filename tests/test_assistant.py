from pathlib import Path
from unittest.mock import patch

import pytest

from src.devsecassistant.assistant import ABSTENTION_MESSAGE, DevSecAssistant

FIXTURES = Path("tests/fixtures")


@pytest.fixture(scope="module")
def assistant():
    return DevSecAssistant(FIXTURES)


def test_answers_password_question(assistant):
    result = assistant.ask("What are the password requirements for external portals?")

    assert result["abstained"] is False
    assert "14 characters" in result["answer"]
    assert any(
        source["source_file"] == "sample_policy.pdf" for source in result["sources"]
    )


def test_rejects_empty_question(assistant):
    with pytest.raises(ValueError, match="question must not be empty"):
        assistant.ask("   ")


def test_rejects_invalid_similarity_threshold():
    with pytest.raises(ValueError, match="min_similarity"):
        DevSecAssistant(
            FIXTURES,
            min_similarity=1.5,
        )


@patch("src.devsecassistant.assistant.build_index")
def test_abstention_returns_simple_message_without_sources(mock_build_index):
    retriever = mock_build_index.return_value
    retriever.search.return_value = [
        {
            "source_file": "sample_policy.pdf",
            "location_type": "page",
            "location": "1",
            "text": "A related passage.",
            "score": 0.8,
        }
    ]

    assistant = DevSecAssistant(FIXTURES)

    with patch(
        "src.devsecassistant.assistant.generate_answer",
        return_value={
            "answer": "The answer is not stated [Source 1: sample_policy.pdf].",
            "sources": [{"source_file": "sample_policy.pdf"}],
            "abstained": True,
            "citation_valid": False,
            "citation_errors": ["Missing citation."],
        },
    ):
        result = assistant.ask("What is not stated?")

    assert result["answer"] == ABSTENTION_MESSAGE
    assert result["sources"] == []
    assert result["abstained"] is True
    assert result["citation_valid"] is None
    assert result["citation_errors"] == []


@patch("src.devsecassistant.assistant.build_index")
def test_no_relevant_passages_returns_simple_message(mock_build_index):
    retriever = mock_build_index.return_value
    retriever.search.return_value = []

    assistant = DevSecAssistant(FIXTURES)
    result = assistant.ask("What is not in the documents?")

    assert result["answer"] == ABSTENTION_MESSAGE
    assert result["sources"] == []
    assert result["abstained"] is True
