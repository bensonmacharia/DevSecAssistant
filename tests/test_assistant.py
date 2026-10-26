from pathlib import Path

import pytest

from src.devsecassistant.assistant import DevSecAssistant

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
