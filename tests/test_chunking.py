import pytest

from src.devsecassistant.chunking import chunk_records


def sample_record(text):
    return {
        "source_file": "password_policy.pdf",
        "file_type": "pdf",
        "location_type": "page",
        "location": "4",
        "text": text,
    }


def test_short_text_produces_one_chunk():
    chunks = chunk_records(
        [sample_record("Passwords must be at least 14 characters.")],
        chunk_size=100,
        overlap=10,
    )

    assert len(chunks) == 1
    assert "14 characters" in chunks[0]["text"]


def test_long_text_produces_overlapping_chunks():
    text = "A" * 2500

    chunks = chunk_records(
        [sample_record(text)],
        chunk_size=1000,
        overlap=150,
    )

    assert len(chunks) == 3
    assert chunks[0]["text"][-150:] == chunks[1]["text"][:150]
    assert chunks[1]["text"][-150:] == chunks[2]["text"][:150]


def test_source_metadata_is_preserved():
    chunks = chunk_records(
        [sample_record("Example security requirement.")],
        chunk_size=100,
        overlap=10,
    )

    assert chunks[0]["source_file"] == "password_policy.pdf"
    assert chunks[0]["location"] == "4"
    assert chunks[0]["chunk_number"] == 1
    assert chunks[0]["chunk_id"]


def test_empty_text_is_skipped():
    assert (
        chunk_records(
            [sample_record("   ")],
            chunk_size=100,
            overlap=10,
        )
        == []
    )


def test_invalid_chunk_size_is_rejected():
    with pytest.raises(ValueError):
        chunk_records([sample_record("Example")], chunk_size=0)


def test_invalid_overlap_is_rejected():
    with pytest.raises(ValueError):
        chunk_records(
            [sample_record("Example")],
            chunk_size=100,
            overlap=100,
        )
