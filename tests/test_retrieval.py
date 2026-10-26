import pytest

from src.devsecassistant.retrieval import SemanticRetriever


def sample_chunks():
    return [
        {
            "source_file": "password_policy.pdf",
            "file_type": "pdf",
            "location_type": "page",
            "location": "2",
            "text": (
                "External portal passwords must contain at least "
                "14 characters and include appropriate complexity."
            ),
            "chunk_id": "password_policy:page:2:1",
        },
        {
            "source_file": "logging_standard.docx",
            "file_type": "docx",
            "location_type": "document",
            "location": "1",
            "text": (
                "Application logs must include a timestamp, severity, "
                "service identifier, and correlation ID."
            ),
            "chunk_id": "logging_standard:document:1:1",
        },
        {
            "source_file": "api_security.pptx",
            "file_type": "pptx",
            "location_type": "slide",
            "location": "3",
            "text": (
                "APIs must validate authorization on every request "
                "and reject unauthorized access."
            ),
            "chunk_id": "api_security:slide:3:1",
        },
    ]


@pytest.fixture(scope="module")
def retriever():
    instance = SemanticRetriever()
    instance.index(sample_chunks())
    return instance


def test_password_question_retrieves_password_policy(retriever):
    results = retriever.search(
        "How long must an external portal password be?",
        top_k=1,
    )

    assert len(results) == 1
    assert results[0]["source_file"] == "password_policy.pdf"
    assert "14 characters" in results[0]["text"]


def test_logging_question_retrieves_logging_standard(retriever):
    results = retriever.search(
        "Which fields must application logs contain?",
        top_k=1,
    )

    assert results[0]["source_file"] == "logging_standard.docx"


def test_retrieval_preserves_source_metadata(retriever):
    results = retriever.search(
        "What are the password requirements?",
        top_k=1,
    )

    assert results[0]["location_type"] == "page"
    assert results[0]["location"] == "2"
    assert "score" in results[0]


def test_search_rejects_empty_query(retriever):
    with pytest.raises(ValueError, match="query must not be empty"):
        retriever.search("   ")


def test_search_rejects_invalid_top_k(retriever):
    with pytest.raises(ValueError, match="top_k must be positive"):
        retriever.search("password requirements", top_k=0)


def test_search_requires_indexing():
    retriever = SemanticRetriever()

    with pytest.raises(RuntimeError, match="Index documents"):
        retriever.search("password requirements")


def test_empty_index_returns_no_results():
    retriever = SemanticRetriever()
    retriever.index([])

    assert retriever.search("password requirements") == []
