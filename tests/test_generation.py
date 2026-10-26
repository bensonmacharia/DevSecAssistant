from src.devsecassistant.generation import indicates_insufficient_evidence


def test_detects_explicit_insufficient_evidence():
    answer = (
        "The retrieved evidence does not provide any information "
        "about API access token requirements."
    )

    assert indicates_insufficient_evidence(answer) is True


def test_detects_explicit_abstention():
    answer = (
        "I could not find sufficiently relevant evidence " "to answer this question."
    )

    assert indicates_insufficient_evidence(answer) is True


def test_does_not_classify_supported_answer_as_abstention():
    answer = "API access tokens must expire after 15 minutes " "[S1]."

    assert indicates_insufficient_evidence(answer) is False


def test_detection_is_case_insensitive_and_handles_whitespace():
    answer = "  THE EVIDENCE IS INSUFFICIENT \n to answer.  "

    assert indicates_insufficient_evidence(answer) is True
