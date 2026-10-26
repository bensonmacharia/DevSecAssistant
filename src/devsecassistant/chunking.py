from typing import Any


def chunk_records(
    records: list[dict[str, Any]],
    chunk_size: int = 1000,
    overlap: int = 150,
) -> list[dict[str, Any]]:
    """
    Split extracted document records into overlapping text chunks.

    chunk_size and overlap are measured in characters in this
    initial implementation, not tokens.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size")

    chunks = []

    for record in records:
        text = record.get("text", "").strip()

        if not text:
            continue

        step = chunk_size - overlap
        start = 0
        chunk_number = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk_text = text[start:end].strip()

            if chunk_text:
                chunk_number += 1

                chunk = {
                    **record,
                    "text": chunk_text,
                    "chunk_id": (
                        f"{record['source_file']}:"
                        f"{record['location_type']}:"
                        f"{record['location']}:"
                        f"{chunk_number}"
                    ),
                    "chunk_number": chunk_number,
                    "chunk_start": start,
                    "chunk_end": end,
                }

                chunks.append(chunk)

            if end == len(text):
                break

            start += step

    return chunks
