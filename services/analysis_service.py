import json
import re

from frontend import clean_section_text
from .groq_service import call_groq_with_retry

RESUME_HEADINGS = {
    "PROFILE SUMMARY",
    "PROFESSIONAL SUMMARY",
    "SUMMARY",
    "EDUCATION",
    "TECHNICAL SKILLS",
    "SKILLS",
    "PROJECTS",
    "EXPERIENCE",
    "WORK EXPERIENCE",
    "CERTIFICATIONS & TRAINING",
    "CERTIFICATIONS",
    "ACHIEVEMENTS & ACTIVITIES",
    "ACHIEVEMENTS",
    "KEY STRENGTHS",
    "STRENGTHS",
    "CONTACT",
}

ANALYSIS_SECTION_ALIASES = {
    "top_suggestions": ["Top 5 Suggestions", "Top Suggestions"],
    "missing_keywords": ["Missing Keywords"],
    "skill_gap_analysis": ["Skill Gap Analysis"],
    "improved_bullets": ["Improved Professional Bullet Points", "Improved Bullet Points"],
}

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "with",
    "you",
    "your",
    "we",
    "our",
    "will",
    "should",
    "must",
    "have",
    "has",
    "had",
    "job",
    "role",
    "description",
    "requirements",
    "responsibilities",
    "preferred",
    "qualification",
    "qualifications",
}


def tokenize_for_overlap(text):
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9+#.-]*", text.lower())
    return {token for token in tokens if len(token) > 2 and token not in STOP_WORDS and not token.isdigit()}


def build_job_description_context(job_role, resume_text):
    word_count = len(re.findall(r"\b\w+\b", job_role or ""))
    if word_count < 8:
        return ""

    job_tokens = tokenize_for_overlap(job_role)
    resume_tokens = tokenize_for_overlap(resume_text)
    if not job_tokens:
        return ""

    overlap = len(job_tokens & resume_tokens) / max(len(job_tokens | resume_tokens), 1)
    missing_keywords = sorted(job_tokens - resume_tokens)
    highlighted_missing = ", ".join(missing_keywords[:20])

    if highlighted_missing:
        return (
            "Job description grounding:\n"
            f"- Overlap similarity: {overlap:.2f}\n"
            f"- Keywords present in the job description but not the resume: {highlighted_missing}"
        )

    return f"Job description grounding:\n- Overlap similarity: {overlap:.2f}"


def normalize_analysis_items(items, limit=None):
    if isinstance(items, str):
        items = re.split(r"\s*,\s*|\s*\n\s*", items)
    elif not isinstance(items, (list, tuple)):
        items = []

    normalized_items = []
    seen = set()

    for item in items or []:
        cleaned_item = re.sub(r"\s+", " ", str(item)).strip(" \t\r\n-•")
        if not cleaned_item:
            continue

        lowered = cleaned_item.lower()
        if lowered in seen:
            continue

        seen.add(lowered)
        normalized_items.append(cleaned_item)
        if limit is not None and len(normalized_items) >= limit:
            break

    return normalized_items


def analysis_json_to_legacy_format(parsed_json) -> dict:
    resume_score = int(parsed_json.get("resume_score", 70) or 0)
    ats_score = int(parsed_json.get("ats_score", 65) or 0)
    job_suitability_score = int(parsed_json.get("job_suitability_score", 60) or 0)

    scores = {
        "Resume Score": max(0, min(100, resume_score)),
        "ATS Score": max(0, min(100, ats_score)),
        "Job Suitability": max(0, min(100, job_suitability_score)),
    }

    top_suggestions = normalize_analysis_items(parsed_json.get("top_suggestions"), limit=5)
    missing_keywords = normalize_analysis_items(parsed_json.get("missing_keywords"), limit=10)
    skill_gap_analysis = normalize_analysis_items(parsed_json.get("skill_gap_analysis"), limit=2)
    improved_bullets = normalize_analysis_items(parsed_json.get("improved_bullets"), limit=3)

    analysis_sections = [
        f"Resume Score: {scores['Resume Score']}",
        f"ATS Score: {scores['ATS Score']}",
        f"Job Suitability Score: {scores['Job Suitability']}",
        "",
        "Top 5 Suggestions",
        "\n".join(f"- {item}" for item in top_suggestions),
        "",
        "Missing Keywords",
        ", ".join(missing_keywords),
        "",
        "Skill Gap Analysis",
        "\n".join(f"- {item}" for item in skill_gap_analysis),
        "",
        "Improved Professional Bullet Points",
        "\n".join(f"- {item}" for item in improved_bullets),
    ]

    analysis_text = "\n".join(part for part in analysis_sections if part is not None).strip()
    return {"analysis": analysis_text, "scores": scores}


def analyze_resume(client, text, job_role):
    job_context = build_job_description_context(job_role, text)
    prompt = f"""
You are a senior ATS recruiter.

Analyze this resume for the job role: {job_role}

Return a single JSON object with this exact schema:
{{
  "resume_score": 0,
  "ats_score": 0,
  "job_suitability_score": 0,
  "top_suggestions": ["...", "...", "...", "...", "..."],
  "missing_keywords": ["...", "..."],
  "skill_gap_analysis": ["...", "..."],
  "improved_bullets": ["...", "...", "..."]
}}

Rules:
- Return JSON only.
- Do not wrap the response in markdown fences.
- Use integers between 0 and 100 for the scores.
- Keep top_suggestions at exactly 5 items.
- Keep missing_keywords between 6 and 10 items.
- Keep skill_gap_analysis at exactly 2 items.
- Keep improved_bullets at exactly 3 items.
- Use short strings in each array item.

{job_context}

Resume:
{text}
"""

    completion = call_groq_with_retry(
        client,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"},
    )
    raw_response = completion.choices[0].message.content

    try:
        parsed_json = json.loads(raw_response)
        if isinstance(parsed_json, dict):
            return analysis_json_to_legacy_format(parsed_json)
    except (TypeError, json.JSONDecodeError):
        pass

    legacy_text = raw_response.strip()
    return {"analysis": legacy_text, "scores": parse_scores(legacy_text)}


def generate_updated_resume(client, text):
    prompt = f"""
You are an expert ATS resume writer.

Rewrite the resume as a polished final resume, but keep all factual information intact.

Rules:
- Return ONLY the final resume content.
- Do NOT include explanations, introductions, notes, or "here is your resume".
- Do NOT include "I made the following changes" or any commentary.
- Preserve contact details, education, projects, certifications, strengths, and skills.
- Use professional section headings.
- Use concise bullet points where appropriate.
- Output plain text only.

Original Resume:
{text}
"""

    completion = call_groq_with_retry(
        client,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return completion.choices[0].message.content


def strip_markdown_links(text):
    return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)


def clean_resume_text(text):
    text = strip_markdown_links(text.replace("\r\n", "\n")).strip()
    text = re.sub(r"^Here(?:'s| is).*$", "", text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r"^I made the following changes.*$", "", text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r"\n\s*\d+\.\s+\*\*.*$", "", text, flags=re.MULTILINE)
    text = text.replace("**", "")
    text = re.sub(r"^[ \t]*[\*\-]\s+", "- ", text, flags=re.MULTILINE)
    text = re.sub(r"^[ \t]*\+\s+", "- ", text, flags=re.MULTILINE)
    text = re.sub(r"[ \t]+", " ", text)

    lines = [line.strip() for line in text.splitlines()]
    cleaned = []
    for line in lines:
        if not line:
            if cleaned and cleaned[-1] != "":
                cleaned.append("")
            continue

        lower = line.lower()
        if lower.startswith("here's a rewritten version") or lower.startswith("i made the following changes"):
            continue
        if re.match(r"^\d+\.\s+", line) and "improved" in lower and "resume" not in lower:
            continue
        cleaned.append(line)

    cleaned_text = "\n".join(cleaned).strip()
    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)
    return cleaned_text


def split_analysis_sections(analysis):
    sections = {
        "top_suggestions": "",
        "missing_keywords": "",
        "skill_gap_analysis": "",
        "improved_bullets": "",
        "other_notes": "",
    }

    score_patterns = [
        r"Resume Score:\s*\d{1,3}",
        r"ATS Score:\s*\d{1,3}",
        r"Job Suitability Score:\s*\d{1,3}",
    ]
    working_text = analysis
    for pattern in score_patterns:
        working_text = re.sub(pattern, "", working_text, flags=re.IGNORECASE)

    heading_matches = []
    for key, aliases in ANALYSIS_SECTION_ALIASES.items():
        alias_pattern = "|".join(re.escape(alias) for alias in aliases)
        pattern = rf"(?im)^\s*(?:{alias_pattern})\s*:?\s*"
        for match in re.finditer(pattern, working_text):
            heading_matches.append((match.start(), match.end(), key))

    heading_matches.sort(key=lambda item: item[0])

    consumed_ranges = []
    for index, (start, end, key) in enumerate(heading_matches):
        next_start = heading_matches[index + 1][0] if index + 1 < len(heading_matches) else len(working_text)
        section_content = working_text[end:next_start]
        cleaned_content = clean_section_text(section_content)
        if cleaned_content and not sections[key]:
            sections[key] = cleaned_content
            consumed_ranges.append((start, next_start))

    other_notes_parts = []
    cursor = 0
    for start, end in consumed_ranges:
        leftover = clean_section_text(working_text[cursor:start])
        if leftover:
            other_notes_parts.append(leftover)
        cursor = end

    trailing_leftover = clean_section_text(working_text[cursor:])
    if trailing_leftover:
        other_notes_parts.append(trailing_leftover)

    sections["other_notes"] = "\n\n".join(part for part in other_notes_parts if part)
    return sections


def parse_scores(result):
    patterns = {
        "Resume Score": r"Resume Score:\s*(\d{1,3})",
        "ATS Score": r"ATS Score:\s*(\d{1,3})",
        "Job Suitability": r"Job Suitability Score:\s*(\d{1,3})",
    }
    defaults = {"Resume Score": 70, "ATS Score": 65, "Job Suitability": 60}

    scores = {}
    for label, pattern in patterns.items():
        match = re.search(pattern, result, flags=re.IGNORECASE)
        value = int(match.group(1)) if match else defaults[label]
        scores[label] = max(0, min(100, value))
    return scores


def extract_keywords_from_analysis(analysis):
    match = re.search(
        r"Missing Keywords\s*:?\s*(.*?)(?:\n[A-Z][A-Za-z ]+\n|\nSkill Gap Analysis|\Z)",
        analysis,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return []
    content = match.group(1)
    items = re.split(r"[\n,â€¢\-]+", content)
    keywords = [item.strip(" :.") for item in items if item.strip(" :.")]  # noqa: E501
    return keywords[:5]
