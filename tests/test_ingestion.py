from pathlib import Path

import pytest

from src.devsecassistant.ingestion import (
    extract_document,
    ingest_directory,
)

FIXTURES = Path("tests/fixtures")


def test_pdf_extraction():
    records = extract_document(FIXTURES / "sample_policy.pdf")

    assert len(records) == 1
    assert records[0]["location_type"] == "page"
    assert records[0]["location"] == "1"
    assert "14 characters" in records[0]["text"]


def test_docx_extraction():
    records = extract_document(FIXTURES / "sample_logging.docx")

    assert len(records) == 1
    assert "structured logging" in records[0]["text"]


def test_pptx_extraction():
    records = extract_document(FIXTURES / "sample_api_security.pptx")

    assert len(records) == 1
    assert records[0]["location_type"] == "slide"
    assert "authentication tokens" in records[0]["text"]


def test_xlsx_extraction():
    records = extract_document(FIXTURES / "sample_audit.xlsx")

    assert len(records) == 1
    assert records[0]["location"] == "Audit Findings"
    assert "Sensitive data in logs" in records[0]["text"]


def test_unsupported_extension(tmp_path):
    unsupported_file = tmp_path / "example.txt"
    unsupported_file.write_text(
        "This is a test file.",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Unsupported document type",
    ):
        extract_document(unsupported_file)


def test_directory_ingestion():
    records = ingest_directory(FIXTURES)

    assert len(records) == 5
    assert {r["file_type"] for r in records} == {
        "pdf",
        "docx",
        "pptx",
        "xlsx",
    }

    source_files = {r["source_file"] for r in records}

    assert source_files == {
        "sample_policy.pdf",
        "sample_logging.docx",
        "sample_api_security.pptx",
        "sample_audit.xlsx",
        "sample_prompt_injection.docx",
    }
