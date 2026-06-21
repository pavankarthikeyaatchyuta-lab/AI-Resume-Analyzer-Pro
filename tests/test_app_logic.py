import json

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
    def __init__(self, content):
        self.content = content
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return FakeCompletion(self.content)


class FakeClient:
    def __init__(self, content):
        self.chat = type("FakeChat", (), {"completions": FakeCompletions(content)})()


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


def test_parse_scores():
    text = sample_legacy_analysis()
    assert app.parse_scores(text) == {
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


def test_analyze_resume_json_and_legacy_paths_match():
    legacy_client = FakeClient(sample_legacy_analysis())
    json_client = FakeClient(json.dumps(sample_json_payload()))

    legacy_result = app.analyze_resume(legacy_client, "resume body", "Machine Learning Engineer")
    json_result = app.analyze_resume(json_client, "resume body", "Machine Learning Engineer")

    assert legacy_client.chat.completions.last_kwargs["response_format"] == {"type": "json_object"}
    assert json_client.chat.completions.last_kwargs["response_format"] == {"type": "json_object"}

    assert legacy_result["scores"] == json_result["scores"]
    assert app.split_analysis_sections(legacy_result["analysis"]) == app.split_analysis_sections(json_result["analysis"])
