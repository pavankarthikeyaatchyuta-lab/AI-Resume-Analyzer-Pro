import json

import httpx
import pytest

import app


class FakeMessage:
    def __init__(self, content):
        self.content = content


class FakeChoice:
    def __init__(self, content):
        self.message = FakeMessage(content)


class FakeCompletion:
    def __init__(self, content):
        self.choices = [FakeChoice(content)]


class FakeCompletions:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if not self.outcomes:
            raise AssertionError("No more outcomes configured")

        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        if callable(outcome):
            outcome = outcome(kwargs)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class FakeClient:
    def __init__(self, outcomes):
        self.chat = type("FakeChat", (), {"completions": FakeCompletions(outcomes)})()


def make_httpx_response(status_code):
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    return httpx.Response(status_code, request=request)


def make_status_error(error_cls, status_code, message="request failed"):
    response = make_httpx_response(status_code)
    return error_cls(message, response=response, body={"error": message})


def sample_legacy_analysis():
    return (
        "Resume Score: 88\n"
        "ATS Score: 84\n"
        "Job Suitability Score: 79\n\n"
        "Top 5 Suggestions\n"
        "- Tailor the summary to the target role.\n"
        "- Add measurable impact to each bullet.\n"
        "- Highlight deployment experience.\n"
        "- Include cloud tooling keywords.\n"
        "- Tighten the skills section.\n\n"
        "Missing Keywords\n"
        "PyTorch, Kubernetes, MLOps, feature engineering, model serving, experiment tracking\n\n"
        "Skill Gap Analysis\n"
        "- Limited evidence of production deployment.\n"
        "- The resume needs stronger cloud and MLOps signals.\n\n"
        "Improved Professional Bullet Points\n"
        "- Built and shipped ML models that improved prediction accuracy by 14%.\n"
        "- Deployed data pipelines and monitoring checks for production workflows.\n"
        "- Partnered with stakeholders to prioritize model requirements.\n"
    )


def sample_json_payload():
    return {
        "resume_score": 88,
        "ats_score": 84,
        "job_suitability_score": 79,
        "top_suggestions": [
            "Tailor the summary to the target role.",
            "Add measurable impact to each bullet.",
            "Highlight deployment experience.",
            "Include cloud tooling keywords.",
            "Tighten the skills section.",
        ],
        "missing_keywords": [
            "PyTorch",
            "Kubernetes",
            "MLOps",
            "feature engineering",
            "model serving",
            "experiment tracking",
        ],
        "skill_gap_analysis": [
            "Limited evidence of production deployment.",
            "The resume needs stronger cloud and MLOps signals.",
        ],
        "improved_bullets": [
            "Built and shipped ML models that improved prediction accuracy by 14%.",
            "Deployed data pipelines and monitoring checks for production workflows.",
            "Partnered with stakeholders to prioritize model requirements.",
        ],
    }


def build_analysis_completion(content):
    return FakeCompletion(content)


def test_parse_scores():
    assert app.parse_scores(sample_legacy_analysis()) == {
        "Resume Score": 88,
        "ATS Score": 84,
        "Job Suitability": 79,
    }


def test_split_analysis_sections():
    sections = app.split_analysis_sections(sample_legacy_analysis())
    assert sections["top_suggestions"].startswith("- Tailor the summary")
    assert "PyTorch" in sections["missing_keywords"]
    assert sections["skill_gap_analysis"].count("- ") == 2
    assert sections["improved_bullets"].count("- ") == 3


def test_extract_keywords_from_analysis():
    keywords = app.extract_keywords_from_analysis(sample_legacy_analysis())
    assert keywords == ["PyTorch", "Kubernetes", "MLOps", "feature engineering", "model serving"]


def test_strip_markdown_links():
    assert app.strip_markdown_links("Visit [OpenAI](https://openai.com) now") == "Visit OpenAI now"


def test_clean_resume_text():
    raw = (
        "Here is your resume\n"
        "**Summary**\n"
        "- [Jane Doe](https://example.com)\n"
        "I made the following changes\n"
    )
    cleaned = app.clean_resume_text(raw)
    assert "Here is your resume" not in cleaned
    assert "I made the following changes" not in cleaned
    assert "[Jane Doe]" not in cleaned
    assert "Jane Doe" in cleaned


def test_analysis_json_to_legacy_format():
    converted = app.analysis_json_to_legacy_format(sample_json_payload())
    assert converted["scores"] == {
        "Resume Score": 88,
        "ATS Score": 84,
        "Job Suitability": 79,
    }

    sections = app.split_analysis_sections(converted["analysis"])
    assert sections["top_suggestions"].count("- ") == 5
    assert "PyTorch, Kubernetes, MLOps" in sections["missing_keywords"]
    assert sections["skill_gap_analysis"].count("- ") == 2
    assert sections["improved_bullets"].count("- ") == 3


def test_retry_helper_succeeds_after_transient_failures(monkeypatch):
    rate_limit = make_status_error(app.RateLimitError, 429, "too many requests")
    client = FakeClient([rate_limit, build_analysis_completion('{"ok": true}')])
    sleep_calls = []
    monkeypatch.setattr(app.time, "sleep", lambda seconds: sleep_calls.append(seconds))

    completion = app.call_groq_with_retry(client, messages=[{"role": "user", "content": "hello"}], response_format={"type": "json_object"})

    assert completion.choices[0].message.content == '{"ok": true}'
    assert sleep_calls == [1]
    assert len(client.chat.completions.calls) == 2


def test_retry_helper_fails_fast_on_bad_request(monkeypatch):
    bad_request = make_status_error(app.BadRequestError, 400, "bad request")
    client = FakeClient([bad_request])
    monkeypatch.setattr(app.time, "sleep", lambda seconds: pytest.fail("sleep should not be called"))

    with pytest.raises(app.BadRequestError):
        app.call_groq_with_retry(client, messages=[{"role": "user", "content": "hello"}])

    assert len(client.chat.completions.calls) == 1


def test_retry_helper_switches_to_fallback_model(monkeypatch):
    model_error = make_status_error(app.APIStatusError, 404, "model not found")
    client = FakeClient([model_error, build_analysis_completion('{"ok": true}')])
    monkeypatch.setattr(app.time, "sleep", lambda seconds: None)

    completion = app.call_groq_with_retry(client, messages=[{"role": "user", "content": "hello"}], response_format={"type": "json_object"})

    assert completion.choices[0].message.content == '{"ok": true}'
    assert client.chat.completions.calls[0]["model"] == app.GROQ_MODEL
    assert client.chat.completions.calls[1]["model"] == app.GROQ_FALLBACK_MODEL


def test_cooldown_blocks_rapid_repeat(monkeypatch):
    fake_time = [100.0]
    warnings = []
    monkeypatch.setattr(app.time, "time", lambda: fake_time[0])
    monkeypatch.setattr(app.st, "warning", lambda message: warnings.append(message))
    app.st.session_state.clear()

    assert app.groq_call_allowed("shared", cooldown_seconds=8) is True
    fake_time[0] = 103.0
    assert app.groq_call_allowed("shared", cooldown_seconds=8) is False
    assert warnings
    assert "Please wait a few seconds" in warnings[0]


def test_analyze_resume_json_and_legacy_paths_match(monkeypatch):
    monkeypatch.setattr(app.time, "sleep", lambda seconds: None)

    legacy_client = FakeClient([build_analysis_completion(sample_legacy_analysis())])
    json_client = FakeClient([build_analysis_completion(json.dumps(sample_json_payload()))])

    legacy_result = app.analyze_resume(legacy_client, "resume body", "Machine Learning Engineer")
    json_result = app.analyze_resume(json_client, "resume body", "Machine Learning Engineer")

    assert legacy_client.chat.completions.calls[0]["response_format"] == {"type": "json_object"}
    assert json_client.chat.completions.calls[0]["response_format"] == {"type": "json_object"}
    assert legacy_result["scores"] == json_result["scores"]
    assert app.split_analysis_sections(legacy_result["analysis"]) == app.split_analysis_sections(json_result["analysis"])
