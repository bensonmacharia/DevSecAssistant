from unittest.mock import patch

import pytest

from src.devsecassistant.two_stage_generation import (
    generate_answer_two_stage,
)


def test_empty_question_is_rejected():
    with pytest.raises(ValueError, match="question must not be empty"):
        generate_answer_two_stage("", [])


def test_no_passages_returns_abstention():
    result = generate_answer_two_stage(
        "What are the API token requirements?",
        [],
    )

    assert result["citation_valid"] is False
    assert result["sources"] == []
    assert "could not find evidence" in result["answer"].lower()


@patch("src.devsecassistant.two_stage_generation.ollama.chat")
def test_malformed_extraction_abstains(mock_chat):
    mock_chat.return_value.message.content = "This is not JSON"

    result = generate_answer_two_stage(
        "What are the API token requirements?",
        [
            {
                "source_file": "sample_policy.pdf",
                "location_type": "page",
                "location": 1,
                "text": "Tokens must expire after 15 minutes.",
                "score": 0.8,
            }
        ],
    )

    assert result["extracted_facts"] == []
    assert result["citation_valid"] is False
    assert "could not establish sufficient relevant facts" in result["answer"].lower()
    assert mock_chat.call_count == 1
