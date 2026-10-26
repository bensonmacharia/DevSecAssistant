import os
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.devsecassistant.assistant import DevSecAssistant

app = FastAPI(
    title="DevSecAssistant API",
    description=("A cybersecurity-focused RAG assistant " "with source-aware answers."),
    version="0.1.0",
)

_assistant_instance: DevSecAssistant | None = None


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=3, ge=1, le=10)


class AskResponse(BaseModel):
    answer: str
    sources: list[dict[str, Any]] = Field(default_factory=list)
    abstained: bool
    retrieved_count: int
    used_evidence_count: int | None = None
    citation_valid: bool | None = None
    citation_errors: list[str] | None = None


def get_assistant() -> DevSecAssistant:
    """Initialize the assistant only when a question is submitted."""
    global _assistant_instance

    if _assistant_instance is None:
        document_directory = Path(os.getenv("DEVSECASSISTANT_DOCUMENTS", "data/raw"))

        try:
            _assistant_instance = DevSecAssistant(document_directory)
        except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
            raise HTTPException(
                status_code=503,
                detail=(
                    "The assistant could not be initialized. "
                    "Check the configured document directory."
                ),
            ) from exc

    return _assistant_instance


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    """Report whether the API process is running."""
    return {
        "status": "ok",
        "service": "DevSecAssistant API",
    }


@app.post("/ask", response_model=AskResponse, tags=["Assistant"])
def ask_question(
    request: AskRequest,
    assistant: DevSecAssistant = Depends(get_assistant),
) -> dict[str, Any]:
    """Answer a question using evidence from indexed documents."""
    if not request.question.strip():
        raise HTTPException(
            status_code=422,
            detail="Question must not be empty or whitespace.",
        )

    try:
        return assistant.ask(
            question=request.question,
            top_k=request.top_k,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
