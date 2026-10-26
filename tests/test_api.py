from fastapi.testclient import TestClient

from src.devsecassistant.api.main import app, get_assistant

client = TestClient(app)


class FakeAssistant:
    """Test double that avoids loading models or calling Ollama."""

    def ask(self, question: str, top_k: int = 3):
        if question == "Unknown question":
            return {
                "answer": "Insufficient evidence.",
                "sources": [],
                "abstained": True,
                "retrieved_count": 0,
            }

        return {
            "answer": "API tokens must expire after 15 minutes.",
            "sources": [{"source_file": "sample_api_security.pptx"}],
            "abstained": False,
            "retrieved_count": 3,
            "used_evidence_count": 1,
            "citation_valid": True,
        }


def setup_function():
    app.dependency_overrides[get_assistant] = lambda: FakeAssistant()


def teardown_function():
    app.dependency_overrides.clear()


def test_health_check_returns_200():
    response = client.get("/health")

    assert response.status_code == 200


def test_health_check_returns_expected_payload():
    response = client.get("/health")

    assert response.json() == {
        "status": "ok",
        "service": "DevSecAssistant API",
    }


def test_api_docs_are_available():
    response = client.get("/docs")

    assert response.status_code == 200


def test_ask_returns_answer_and_sources():
    response = client.post(
        "/ask",
        json={"question": "What is the token expiry?"},
    )

    assert response.status_code == 200

    body = response.json()
    assert "15 minutes" in body["answer"]
    assert body["sources"][0]["source_file"] == ("sample_api_security.pptx")
    assert body["abstained"] is False
    assert body["citation_valid"] is True


def test_ask_passes_top_k_to_assistant():
    class RecordingAssistant(FakeAssistant):
        def ask(self, question: str, top_k: int = 3):
            assert top_k == 5
            return super().ask(question, top_k)

    app.dependency_overrides[get_assistant] = lambda: RecordingAssistant()

    response = client.post(
        "/ask",
        json={"question": "What is the token expiry?", "top_k": 5},
    )

    assert response.status_code == 200


def test_ask_preserves_abstention():
    response = client.post(
        "/ask",
        json={"question": "Unknown question"},
    )

    assert response.status_code == 200
    assert response.json()["abstained"] is True
    assert response.json()["sources"] == []


def test_ask_rejects_blank_question():
    response = client.post(
        "/ask",
        json={"question": "   "},
    )

    assert response.status_code == 422


def test_ask_rejects_top_k_above_limit():
    response = client.post(
        "/ask",
        json={"question": "Test question", "top_k": 11},
    )

    assert response.status_code == 422
