from src.devsecassistant.citation_validation import (
    validate_and_format_citations,
)


def sample_passages():
    return [
        {
            "source_file": "sample_policy.pdf",
            "location_type": "page",
            "location": "1",
        },
        {
            "source_file": "sample_api_security.pptx",
            "location_type": "slide",
            "location": "1",
        },
    ]


def test_valid_citation_is_formatted_from_metadata():
    result = validate_and_format_citations(
        "Passwords require at least 14 characters [S1].",
        sample_passages(),
    )

    assert result["citation_valid"] is True
    assert result["citation_errors"] == []
    assert "[Source 1: sample_policy.pdf, page 1]" in result["answer"]


def test_invalid_citation_is_flagged():
    result = validate_and_format_citations(
        "The requirement is 14 characters [S9].",
        sample_passages(),
    )

    assert result["citation_valid"] is False
    assert any("Invalid citation [S9]" in error for error in result["citation_errors"])


def test_missing_citation_is_flagged():
    result = validate_and_format_citations(
        "Passwords require at least 14 characters.",
        sample_passages(),
    )

    assert result["citation_valid"] is False
    assert any(
        "no evidence citations" in error.lower() for error in result["citation_errors"]
    )


def test_multiple_valid_citations_are_formatted():
    result = validate_and_format_citations(
        "See the policy [S1] and API guidance [S2].",
        sample_passages(),
    )

    assert result["citation_valid"] is True
    assert "sample_policy.pdf, page 1" in result["answer"]
    assert "sample_api_security.pptx, slide 1" in result["answer"]


def test_mixed_valid_and_invalid_citations_are_flagged():
    result = validate_and_format_citations(
        "The policy says 14 characters [S1], with more details in [S9].",
        sample_passages(),
    )

    assert result["citation_valid"] is False
    assert "sample_policy.pdf, page 1" in result["answer"]
    assert "[S9]" in result["answer"]
