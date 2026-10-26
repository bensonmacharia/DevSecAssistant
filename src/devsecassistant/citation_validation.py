import re
from typing import Any

CITATION_PATTERN = re.compile(r"\[S(\d+)\]")


def validate_and_format_citations(
    answer: str,
    passages: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Validate evidence IDs in an answer and format valid citations
    using metadata from the retrieved passages.
    """
    matches = list(CITATION_PATTERN.finditer(answer))
    cited_ids = [int(match.group(1)) for match in matches]
    errors: list[str] = []

    if not cited_ids:
        errors.append("The answer contains no evidence citations.")

    for citation_id in sorted(set(cited_ids)):
        if citation_id < 1 or citation_id > len(passages):
            errors.append(
                f"Invalid citation [S{citation_id}]: "
                "no matching evidence passage was supplied."
            )

    def format_citation(match: re.Match[str]) -> str:
        citation_id = int(match.group(1))

        if citation_id < 1 or citation_id > len(passages):
            return match.group(0)

        passage = passages[citation_id - 1]
        source_file = passage.get("source_file", "Unknown source")
        location_type = passage.get("location_type", "")
        location = passage.get("location", "")

        if location_type in {"page", "slide"}:
            location_text = f"{location_type} {location}"
        elif location_type == "worksheet":
            location_text = f"worksheet {location}"
        elif location_type == "document":
            location_text = "document body"
        elif location:
            location_text = f"{location_type} {location}".strip()
        else:
            location_text = "location unspecified"

        return f"[Source {citation_id}: {source_file}, {location_text}]"

    formatted_answer = CITATION_PATTERN.sub(format_citation, answer)

    return {
        "answer": formatted_answer,
        "citation_valid": not errors,
        "citation_errors": errors,
    }
