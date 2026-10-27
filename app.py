from pathlib import Path
import logging

import streamlit as st

from src.devsecassistant.assistant import ABSTENTION_MESSAGE, DevSecAssistant

# --------------------------------------------------
# Configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent
DOCUMENT_DIRECTORY = PROJECT_ROOT / "data" / "raw"

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".xlsx"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB per file

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="DevSecAssistant",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------
# Reusable UI functions
# --------------------------------------------------


def display_sources(sources: list[dict]) -> None:
    """Display source metadata and retrieval similarity scores."""
    if not sources:
        return

    with st.expander(f"View sources ({len(sources)})"):
        for index, source in enumerate(sources, start=1):
            filename = source.get("source_file", "Unknown source")
            location_type = source.get("location_type", "")
            location = source.get("location", "")
            score = source.get("score")

            if location_type == "document":
                location_label = "Document body"
            elif location_type == "worksheet" and location:
                location_label = f"Worksheet: {location}"
            elif location_type and location:
                location_label = f"{location_type.title()} {location}"
            else:
                location_label = "Location unspecified"

            st.markdown(f"**{index}. {filename}**")
            st.caption(f"Location: {location_label}")

            if score is not None:
                st.caption(f"Retrieval similarity: {score:.3f}")

            if index < len(sources):
                st.divider()


def display_message(message: dict) -> None:
    """Render a conversation message and its associated metadata."""
    with st.chat_message(message["role"]):
        abstained = message.get("role") == "assistant" and message.get("abstained")
        st.markdown(ABSTENTION_MESSAGE if abstained else message["content"])

        if message["role"] != "assistant" or abstained:
            return

        display_sources(message.get("sources", []))

        if message.get("citation_valid") is False:
            st.warning(
                "The answer's citations could not be fully validated. "
                "Check the citation details before relying on the answer."
            )


def get_supported_documents() -> list[Path]:
    """Return supported files directly inside the document directory."""
    if not DOCUMENT_DIRECTORY.is_dir():
        return []

    return sorted(
        (
            path
            for path in DOCUMENT_DIRECTORY.iterdir()
            if path.is_file() and path.suffix.lower() in ALLOWED_EXTENSIONS
        ),
        key=lambda path: path.name.lower(),
    )


def save_uploaded_documents(
    uploaded_files,
) -> tuple[list[str], list[str], list[str]]:
    """
    Save uploaded files without overwriting existing files.

    Returns:
        saved: filenames saved successfully.
        skipped: filenames skipped because they already exist.
        rejected: filenames rejected or not saved.
    """
    saved = []
    skipped = []
    rejected = []

    DOCUMENT_DIRECTORY.mkdir(parents=True, exist_ok=True)

    for uploaded_file in uploaded_files:
        filename = Path(uploaded_file.name).name
        extension = Path(filename).suffix.lower()

        if (
            not filename
            or filename in {".", ".."}
            or extension not in ALLOWED_EXTENSIONS
        ):
            rejected.append(f"{filename or 'Unknown file'}: unsupported file type.")
            continue

        content = uploaded_file.getvalue()

        if not content:
            rejected.append(f"{filename}: file is empty.")
            continue

        if len(content) > MAX_FILE_SIZE:
            rejected.append(f"{filename}: exceeds the 50 MB per-file limit.")
            continue

        destination = DOCUMENT_DIRECTORY / filename

        try:
            # Exclusive creation prevents accidental overwrites.
            with destination.open("xb") as file:
                file.write(content)

            saved.append(filename)

        except FileExistsError:
            skipped.append(f"{filename}: a file with this name already exists.")

        except OSError:
            logger.exception("Could not save uploaded file: %s", filename)
            rejected.append(
                f"{filename}: could not save the file. Check application logs."
            )

    return saved, skipped, rejected


# --------------------------------------------------
# Session state
# --------------------------------------------------

if "assistant" not in st.session_state:
    st.session_state.assistant = None

if "messages" not in st.session_state:
    st.session_state.messages = []


# --------------------------------------------------
# Sidebar
# --------------------------------------------------

with st.sidebar:
    st.title("🛡️ DevSecAssistant")
    st.caption("Local cybersecurity knowledge assistant")

    if st.button(
        "＋ New chat",
        use_container_width=True,
        type="primary",
    ):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    st.subheader("Settings")

    top_k = st.slider(
        "Retrieved passages",
        min_value=1,
        max_value=10,
        value=3,
        help=(
            "Maximum number of passages retrieved for each question. "
            "The relevance threshold may exclude some passages."
        ),
    )

    st.divider()

    # ----------------------------------------------
    # Document upload and indexing
    # ----------------------------------------------

    st.subheader("Knowledge base")
    st.caption("Document directory")
    st.code("data/raw/", language=None)

    supported_documents = get_supported_documents()

    st.metric("Supported documents", len(supported_documents))

    with st.expander("View indexed document files"):
        if supported_documents:
            for document in supported_documents:
                st.caption(f"📄 {document.name}")
        else:
            st.caption("No supported documents found.")

    uploaded_files = st.file_uploader(
        "Upload security documents",
        type=["pdf", "docx", "pptx", "xlsx"],
        accept_multiple_files=True,
        help=(
            "Supported formats: PDF, DOCX, PPTX, and XLSX. " "Maximum 50 MB per file."
        ),
        key="document_uploader",
    )

    index_documents = st.button(
        "Upload and index documents",
        use_container_width=True,
        disabled=not uploaded_files,
    )

    if index_documents and uploaded_files:
        saved, skipped, rejected = save_uploaded_documents(uploaded_files)

        for filename in saved:
            st.success(f"Uploaded: {filename}")

        for message in skipped:
            st.warning(message)

        for message in rejected:
            st.error(message)

        if saved:
            # Keep a reference to the previous working assistant.
            previous_assistant = st.session_state.assistant

            with st.spinner("Rebuilding the search index. This may take a while..."):
                try:
                    new_assistant = DevSecAssistant(
                        document_directory=DOCUMENT_DIRECTORY,
                    )

                    # Replace the current assistant only after successful
                    # initialization of the new index.
                    st.session_state.assistant = new_assistant

                    st.session_state["upload_status"] = (
                        f"Successfully indexed the knowledge base. "
                        f"{len(saved)} new document(s) were added."
                    )

                except Exception:
                    logger.exception("Failed to rebuild the document index.")

                    # Keep the previous assistant if it is still available.
                    st.session_state.assistant = previous_assistant

                    st.session_state["upload_error"] = (
                        "The files were saved, but rebuilding the index "
                        "failed. The previous assistant has been retained "
                        "if it was available. Check the terminal logs."
                    )

            # Rerun to refresh the document list and show indexing status.
            st.rerun()

        elif skipped or rejected:
            st.info("No new documents were added to the index.")

    if st.session_state.get("upload_status"):
        st.success(st.session_state.pop("upload_status"))

    if st.session_state.get("upload_error"):
        st.error(st.session_state.pop("upload_error"))

    st.caption(
        "Uploaded files are saved locally. Only upload documents "
        "you are authorized to process."
    )

    st.divider()

    # ----------------------------------------------
    # System information
    # ----------------------------------------------

    st.subheader("System")
    st.caption("Language model: Ollama")
    st.caption("Retrieval: Semantic search")
    st.caption("Answer generation: Local RAG pipeline")

    st.divider()

    st.caption(
        "Answers can be incomplete or incorrect. "
        "Verify important security decisions against original sources."
    )


# --------------------------------------------------
# Main interface
# --------------------------------------------------

st.title("Cybersecurity Knowledge Assistant")
st.caption(
    "Ask questions about your indexed security policies, standards, "
    "procedures, and technical documentation."
)


# --------------------------------------------------
# Initialize the assistant
# --------------------------------------------------

if st.session_state.assistant is None:
    with st.spinner("Loading documents and embedding model..."):
        try:
            st.session_state.assistant = DevSecAssistant(
                document_directory=DOCUMENT_DIRECTORY,
            )

        except Exception:
            logger.exception("Could not initialize DevSecAssistant.")

            st.error(
                "DevSecAssistant could not be initialized. "
                "Check that data/raw contains supported documents "
                "with extractable text and that the embedding model "
                "is available."
            )
            st.info("Review the terminal running Streamlit for details.")
            st.stop()


# --------------------------------------------------
# Welcome message and conversation history
# --------------------------------------------------

if not st.session_state.messages:
    st.info(
        "Ask a cybersecurity question to get started. "
        "Answers are based on evidence retrieved from your indexed documents."
    )

for message in st.session_state.messages:
    display_message(message)


# --------------------------------------------------
# Chat input and answer generation
# --------------------------------------------------

question = st.chat_input("Ask a cybersecurity question...")

if question and question.strip():
    question = question.strip()

    user_message = {
        "role": "user",
        "content": question,
    }

    st.session_state.messages.append(user_message)
    display_message(user_message)

    with st.chat_message("assistant"):
        with st.spinner("Searching documents and generating an answer..."):
            try:
                result = st.session_state.assistant.ask(
                    question,
                    top_k=top_k,
                )

                answer = result.get(
                    "answer",
                    "No answer was returned by the assistant.",
                )

                assistant_message = {
                    "role": "assistant",
                    "content": answer,
                    "sources": result.get("sources", []),
                    "abstained": result.get("abstained", False),
                    "citation_valid": result.get("citation_valid"),
                    "citation_errors": result.get("citation_errors", []),
                }

                st.markdown(answer)

                if not assistant_message["abstained"]:
                    display_sources(assistant_message["sources"])

                    if assistant_message["citation_valid"] is False:
                        st.warning(
                            "The answer's citations could not be fully "
                            "validated. Check the citation details."
                        )

                st.session_state.messages.append(assistant_message)

            except Exception:
                logger.exception("Error while answering a user question.")

                error_message = (
                    "I encountered an error while processing your question. "
                    "Please check the application logs and try again."
                )

                st.error(error_message)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_message,
                        "sources": [],
                        "abstained": False,
                    }
                )
