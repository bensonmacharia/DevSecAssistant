from pathlib import Path

import streamlit as st

from src.devsecassistant.assistant import DevSecAssistant

# --------------------------------------------------
# Configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent
DOCUMENT_DIRECTORY = PROJECT_ROOT / "data" / "raw"

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
    """Display retrieved source metadata in an expandable section."""
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
    """Render one conversation message and its associated metadata."""
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message["role"] != "assistant":
            return

        if message.get("abstained"):
            st.warning(
                "The indexed documents do not contain sufficient "
                "evidence to answer this question."
            )

        display_sources(message.get("sources", []))

        if message.get("citation_valid") is False:
            st.warning(
                "The answer's citations could not be fully validated. "
                "Check the citation details before relying on the answer."
            )


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

    st.subheader("Knowledge base")
    st.caption("Document directory")
    st.code("data/raw/", language=None)

    st.caption(
        "Supported document formats depend on the current ingestion " "pipeline."
    )

    st.divider()

    st.subheader("System")
    st.caption("Language model: Ollama")
    st.caption("Retrieval: Semantic search")
    st.caption("Answer generation: Local RAG pipeline")

    st.divider()

    st.caption(
        "Answers can be incomplete or incorrect. "
        "Verify important security decisions against the original sources."
    )


# --------------------------------------------------
# Main interface
# --------------------------------------------------

st.title("Cybersecurity Knowledge Assistant")
st.caption(
    "Ask questions about your indexed security policies, standards, "
    "procedures, and technical documentation."
)

# Initialize the assistant once per Streamlit session.
if st.session_state.assistant is None:
    with st.spinner("Loading documents and embedding model..."):
        try:
            st.session_state.assistant = DevSecAssistant(
                document_directory=DOCUMENT_DIRECTORY,
            )
        except Exception:
            st.error(
                "DevSecAssistant could not be initialized. "
                "Check that data/raw contains supported documents "
                "with extractable text and that the embedding model "
                "is available."
            )
            st.info(
                "Review the terminal running Streamlit for the "
                "underlying error details."
            )
            st.stop()

# Show a welcome message when the conversation is empty.
if not st.session_state.messages:
    st.info(
        "Ask a cybersecurity question to get started. "
        "Answers are based on evidence retrieved from your indexed documents."
    )

# Render conversation history.
for message in st.session_state.messages:
    display_message(message)

# Chat input.
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

                if assistant_message["abstained"]:
                    st.warning(
                        "The indexed documents do not contain sufficient "
                        "evidence to answer this question."
                    )

                display_sources(assistant_message["sources"])

                if assistant_message["citation_valid"] is False:
                    st.warning(
                        "The answer's citations could not be fully "
                        "validated. Check the citation details."
                    )

                st.session_state.messages.append(assistant_message)

            except Exception:
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
