import html
import re

import streamlit as st


def clean_section_text(text):
    # Normalize common LLM formatting quirks so every analysis block renders consistently.
    text = text.strip()
    text = text.replace("**", "")
    text = re.sub(r"^[ \t]*\+\s+", "- ", text, flags=re.MULTILINE)
    text = re.sub(r"^[ \t]*[\u2022]\s+", "- ", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+[.)]\s+", "- ", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_list_items(text):
    # Collapse wrapped bullet lines back into single list items before rendering them in Streamlit.
    cleaned = clean_section_text(text)
    items = []
    current_item = None
    has_bullets = any(line.strip().startswith("- ") for line in cleaned.splitlines())

    for raw_line in cleaned.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("- "):
            if current_item:
                items.append(current_item.strip())
            current_item = line[2:].strip()
            continue

        if current_item:
            current_item = f"{current_item} {line}".strip()
        elif not has_bullets:
            items.append(line)

    if current_item:
        items.append(current_item.strip())

    normalized_items = []
    for item in items:
        item = re.sub(r"\s+", " ", item).strip(" -")
        if item:
            normalized_items.append(item)

    return normalized_items


def extract_keyword_items(text):
    # Keywords are displayed as chips, so convert mixed comma/newline output into unique short tokens.
    cleaned = clean_section_text(text).replace("\n", ", ")
    raw_items = re.split(r"\s*,\s*|\s*;\s*", cleaned)
    keywords = []
    seen = set()

    for item in raw_items:
        normalized = item.strip(" .:-")
        normalized_key = normalized.lower()
        if normalized and normalized_key not in seen:
            keywords.append(normalized)
            seen.add(normalized_key)

    return keywords


def split_into_sentences(text):
    cleaned = clean_section_text(text).replace("\n", " ")
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    return [part.strip() for part in parts if part.strip()]


def render_report_block(title, content, variant="text"):
    if not content:
        return

    with st.container(border=True):
        st.markdown(f"#### {title}")

        # Each variant preserves the same block layout while changing only the internal presentation.
        if variant == "list":
            items = extract_list_items(content)
            if items:
                st.markdown("\n".join(f"- {item}" for item in items))
                return

        if variant == "keywords":
            keywords = extract_keyword_items(content)
            if keywords:
                chips = "".join(f'<span class="keyword-chip">{html.escape(keyword)}</span>' for keyword in keywords)
                st.markdown(f'<div class="keyword-cloud">{chips}</div>', unsafe_allow_html=True)
                return

        if variant == "insights":
            items = extract_list_items(content)
            if len(items) <= 1:
                items = split_into_sentences(content)
            if items:
                st.markdown("\n".join(f"- {item}" for item in items))
                return

        st.markdown(clean_section_text(content))


def score_summary(score):
    if score >= 85:
        return "Excellent"
    if score >= 70:
        return "Strong"
    if score >= 55:
        return "Average"
    return "Needs work"


def render_styles():
    # Centralize the visual theme here so app.py can focus on behavior and data flow.
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Manrope:wght@400;500;700;800&display=swap');

        .stApp {
            background:
                radial-gradient(circle at 18% 22%, rgba(103, 232, 249, 0.18), transparent 16%),
                radial-gradient(circle at 82% 10%, rgba(139, 92, 246, 0.22), transparent 18%),
                radial-gradient(circle at 60% 78%, rgba(245, 158, 11, 0.13), transparent 18%),
                radial-gradient(circle at 40% 52%, rgba(37, 99, 235, 0.10), transparent 24%),
                linear-gradient(180deg, #01040d 0%, #050b18 38%, #091224 100%);
            color: #e5eefc;
            font-family: 'Manrope', sans-serif;
        }

        .stApp::before,
        .stApp::after {
            content: "";
            position: fixed;
            inset: 0;
            pointer-events: none;
            z-index: 0;
        }

        .stApp::before {
            background-image:
                radial-gradient(2px 2px at 8% 12%, rgba(255,255,255,0.9), transparent 60%),
                radial-gradient(1.5px 1.5px at 24% 28%, rgba(255,255,255,0.75), transparent 60%),
                radial-gradient(2px 2px at 42% 18%, rgba(103,232,249,0.8), transparent 60%),
                radial-gradient(1.5px 1.5px at 64% 34%, rgba(255,255,255,0.78), transparent 60%),
                radial-gradient(2px 2px at 78% 16%, rgba(139,92,246,0.8), transparent 60%),
                radial-gradient(1.5px 1.5px at 88% 42%, rgba(255,255,255,0.8), transparent 60%),
                radial-gradient(2px 2px at 16% 76%, rgba(245,158,11,0.7), transparent 60%),
                radial-gradient(1.5px 1.5px at 56% 68%, rgba(255,255,255,0.76), transparent 60%),
                radial-gradient(2px 2px at 72% 82%, rgba(103,232,249,0.85), transparent 60%);
            animation: twinkle 8s ease-in-out infinite alternate;
            opacity: 0.9;
        }

        .stApp::after {
            background:
                radial-gradient(circle at 50% -10%, rgba(103,232,249,0.10), transparent 30%),
                radial-gradient(circle at 100% 0%, rgba(139,92,246,0.09), transparent 24%);
            filter: blur(30px);
        }

        .space-layer {
            position: fixed;
            inset: 0;
            pointer-events: none;
            z-index: 0;
            overflow: hidden;
        }

        .space-nebula,
        .space-nebula-two,
        .space-nebula-three {
            position: absolute;
            border-radius: 50%;
            filter: blur(28px);
            opacity: 0.85;
        }

        .space-nebula {
            width: 520px;
            height: 520px;
            top: -110px;
            left: -120px;
            background: radial-gradient(circle, rgba(103,232,249,0.18), rgba(37,99,235,0.06) 48%, transparent 72%);
            animation: nebulaDrift 18s ease-in-out infinite alternate;
        }

        .space-nebula-two {
            width: 620px;
            height: 620px;
            top: 8%;
            right: -180px;
            background: radial-gradient(circle, rgba(139,92,246,0.22), rgba(76,29,149,0.08) 50%, transparent 74%);
            animation: nebulaDriftReverse 22s ease-in-out infinite alternate;
        }

        .space-nebula-three {
            width: 460px;
            height: 460px;
            bottom: -120px;
            left: 32%;
            background: radial-gradient(circle, rgba(245,158,11,0.14), rgba(217,70,239,0.05) 48%, transparent 74%);
            animation: pulseNebula 12s ease-in-out infinite;
        }

        .space-grid {
            position: absolute;
            inset: 0;
            background-image:
                linear-gradient(rgba(103,232,249,0.05) 1px, transparent 1px),
                linear-gradient(90deg, rgba(103,232,249,0.05) 1px, transparent 1px);
            background-size: 120px 120px;
            mask-image: radial-gradient(circle at center, rgba(255,255,255,0.38), transparent 72%);
            opacity: 0.28;
            transform: perspective(800px) rotateX(68deg) translateY(32%);
            transform-origin: bottom;
        }

        .space-orbit,
        .space-orbit-two,
        .space-orbit-three,
        .space-orbit-four {
            position: absolute;
            border-radius: 50%;
            border: 1px solid rgba(103,232,249,0.14);
            box-shadow: 0 0 60px rgba(103,232,249,0.08), inset 0 0 40px rgba(139,92,246,0.05);
        }

        .space-orbit {
            width: 640px;
            height: 640px;
            top: -170px;
            right: -140px;
            animation: orbitSpin 26s linear infinite;
        }

        .space-orbit-two {
            width: 460px;
            height: 460px;
            bottom: 6%;
            left: -120px;
            animation: orbitSpinReverse 20s linear infinite;
        }

        .space-orbit-three {
            width: 280px;
            height: 280px;
            top: 34%;
            right: 16%;
            animation: pulseFloat 7s ease-in-out infinite;
        }

        .space-orbit-four {
            width: 760px;
            height: 760px;
            bottom: -320px;
            right: 10%;
            animation: orbitSpinReverse 34s linear infinite;
        }

        .space-planet,
        .space-planet-two,
        .space-planet-three {
            position: absolute;
            border-radius: 50%;
            filter: blur(0.2px);
        }

        .space-planet {
            width: 18px;
            height: 18px;
            top: 60px;
            left: 120px;
            background: radial-gradient(circle at 30% 30%, #67e8f9, #2563eb 70%);
            box-shadow: 0 0 24px rgba(103,232,249,0.55);
        }

        .space-planet-two {
            width: 22px;
            height: 22px;
            bottom: 42px;
            right: 72px;
            background: radial-gradient(circle at 35% 35%, #f59e0b, #7c3aed 75%);
            box-shadow: 0 0 28px rgba(245,158,11,0.42);
        }

        .space-planet-three {
            width: 12px;
            height: 12px;
            top: 28px;
            right: 26px;
            background: radial-gradient(circle at 35% 35%, #ffffff, #67e8f9 75%);
            box-shadow: 0 0 18px rgba(255,255,255,0.55);
        }

        .shooting-star,
        .shooting-star-two,
        .shooting-star-three,
        .shooting-star-four {
            position: absolute;
            width: 260px;
            height: 3px;
            background: linear-gradient(90deg, rgba(255,255,255,0), rgba(255,255,255,0.95), rgba(103,232,249,0));
            transform: rotate(-18deg);
            opacity: 0;
            filter: drop-shadow(0 0 10px rgba(103,232,249,0.45));
        }

        .shooting-star {
            top: 18%;
            left: 58%;
            animation: shooting 9s linear infinite;
        }

        .shooting-star-two {
            top: 52%;
            left: 16%;
            animation: shooting 12s linear infinite 2s;
        }

        .shooting-star-three {
            top: 72%;
            left: 70%;
            animation: shooting 10s linear infinite 5s;
        }

        .shooting-star-four {
            top: 26%;
            left: 32%;
            animation: shootingLong 14s linear infinite 1s;
        }

        @keyframes twinkle {
            from { opacity: 0.45; transform: translateY(0px); }
            to { opacity: 0.95; transform: translateY(6px); }
        }

        @keyframes orbitSpin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        @keyframes orbitSpinReverse {
            from { transform: rotate(360deg); }
            to { transform: rotate(0deg); }
        }

        @keyframes pulseFloat {
            0%, 100% { transform: translateY(0px) scale(1); opacity: 0.55; }
            50% { transform: translateY(-12px) scale(1.04); opacity: 0.9; }
        }

        @keyframes nebulaDrift {
            from { transform: translate3d(0, 0, 0) scale(1); }
            to { transform: translate3d(40px, 22px, 0) scale(1.08); }
        }

        @keyframes nebulaDriftReverse {
            from { transform: translate3d(0, 0, 0) scale(1); }
            to { transform: translate3d(-44px, 28px, 0) scale(1.1); }
        }

        @keyframes pulseNebula {
            0%, 100% { opacity: 0.45; transform: scale(1); }
            50% { opacity: 0.88; transform: scale(1.12); }
        }

        @keyframes shooting {
            0% { transform: translateX(0) translateY(0) rotate(-18deg); opacity: 0; }
            8% { opacity: 1; }
            24% { transform: translateX(-300px) translateY(160px) rotate(-18deg); opacity: 0; }
            100% { transform: translateX(-300px) translateY(160px) rotate(-18deg); opacity: 0; }
        }

        @keyframes shootingLong {
            0% { transform: translateX(0) translateY(0) rotate(-24deg); opacity: 0; }
            10% { opacity: 1; }
            28% { transform: translateX(-420px) translateY(220px) rotate(-24deg); opacity: 0; }
            100% { transform: translateX(-420px) translateY(220px) rotate(-24deg); opacity: 0; }
        }

        .main .block-container {
            position: relative;
            z-index: 1;
            max-width: 1180px;
            padding-top: 1.35rem;
            padding-bottom: 2rem;
        }

        h1, h2, h3, [data-testid="stMetricLabel"] {
            font-family: 'Space Grotesk', sans-serif !important;
            color: #f8fbff !important;
        }

        p, li, label, .stCaption {
            color: #b9c8dc !important;
        }

        [data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, rgba(6,11,24,0.98) 0%, rgba(10,18,35,0.98) 100%);
            border-right: 1px solid rgba(148,163,184,0.12);
        }

        [data-testid="stSidebar"] * {
            color: #e5eefc;
        }

        [data-testid="stSidebar"] .stFileUploader,
        [data-testid="stSidebar"] .stTextInput,
        [data-testid="stSidebar"] .stSelectbox {
            background: rgba(15, 23, 42, 0.72);
            border-radius: 18px;
            padding: 0.2rem;
            border: 1px solid rgba(148,163,184,0.12);
        }

        [data-testid="stSidebar"] .stButton > button {
            border-radius: 999px;
            min-height: 3rem;
            font-weight: 800;
            border: none;
            background: linear-gradient(135deg, #8b5cf6 0%, #2563eb 100%);
            color: white !important;
        }

        [data-testid="stSidebar"] .stButton:last-of-type > button {
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(148,163,184,0.18);
        }

        .hero-card, .glass-card {
            background: linear-gradient(180deg, rgba(10,18,35,0.82) 0%, rgba(15,23,42,0.74) 100%);
            border: 1px solid rgba(148,163,184,0.12);
            box-shadow: 0 20px 50px rgba(0,0,0,0.22);
            backdrop-filter: blur(16px);
            border-radius: 24px;
        }

        .hero-card {
            position: relative;
            overflow: hidden;
            padding: 2rem 2.1rem;
            margin-bottom: 1rem;
            min-height: 290px;
        }

        .hero-card::before {
            content: "";
            position: absolute;
            inset: -20% auto auto -10%;
            width: 460px;
            height: 460px;
            background: radial-gradient(circle, rgba(103,232,249,0.12), transparent 60%);
            filter: blur(20px);
        }

        .hero-card::after {
            content: "";
            position: absolute;
            top: -60px;
            right: -40px;
            width: 320px;
            height: 320px;
            background: radial-gradient(circle, rgba(139,92,246,0.20), transparent 62%);
            filter: blur(14px);
        }

        .hero-grid {
            position: relative;
            z-index: 1;
            display: grid;
            grid-template-columns: 1.35fr 0.65fr;
            gap: 1rem;
            align-items: end;
        }

        .hero-kicker {
            display: inline-block;
            padding: 0.35rem 0.75rem;
            border-radius: 999px;
            background: rgba(103,232,249,0.10);
            color: #67e8f9;
            font-size: 0.72rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.8rem;
        }

        .hero-title {
            font-family: 'Space Grotesk', sans-serif;
            font-size: clamp(2.4rem, 5vw, 5rem);
            line-height: 0.95;
            margin: 0 0 0.55rem 0;
            font-weight: 700;
            color: #f8fbff;
            max-width: 760px;
            text-wrap: balance;
        }

        .hero-copy {
            color: #b9c8dc;
            font-size: 1.02rem;
            line-height: 1.7;
            margin: 0;
            max-width: 760px;
        }

        .glass-card {
            padding: 1rem 1.1rem;
        }

        .hero-signal {
            justify-self: end;
            width: 100%;
            max-width: 290px;
            padding: 1.15rem 1.2rem;
            border-radius: 24px;
            background: linear-gradient(180deg, rgba(5,10,22,0.86), rgba(15,23,42,0.84));
            border: 1px solid rgba(103,232,249,0.16);
            box-shadow: 0 0 40px rgba(103,232,249,0.08), inset 0 0 30px rgba(139,92,246,0.06);
        }

        .hero-signal-label {
            color: #67e8f9;
            text-transform: uppercase;
            letter-spacing: 0.09em;
            font-size: 0.72rem;
            font-weight: 800;
            margin-bottom: 0.55rem;
        }

        .hero-signal-score {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 4rem;
            line-height: 0.95;
            color: #f8fbff;
            margin-bottom: 0.45rem;
        }

        .hero-signal-note {
            color: #b9c8dc;
            font-size: 0.95rem;
            line-height: 1.5;
        }

        .panel-title {
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 700;
            font-size: 1rem;
            margin-bottom: 0.25rem;
            color: #f8fbff;
        }

        .panel-copy {
            color: #b9c8dc;
            line-height: 1.6;
            font-size: 0.95rem;
        }

        .report-card {
            height: 100%;
            padding: 1.25rem 1.3rem;
            border-radius: 22px;
            background: linear-gradient(180deg, rgba(10,18,35,0.82) 0%, rgba(15,23,42,0.72) 100%);
            border: 1px solid rgba(148,163,184,0.16);
            box-shadow: 0 14px 36px rgba(0,0,0,0.18);
        }

        .report-card-title {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1.18rem;
            font-weight: 700;
            color: #f8fbff;
            margin-bottom: 1rem;
        }

        .report-copy {
            color: #c7d2e4;
            line-height: 1.75;
            margin: 0 0 0.65rem 0;
        }

        .report-list {
            margin: 0;
            padding-left: 1.2rem;
            color: #d6e1f0;
        }

        .report-list li {
            margin-bottom: 0.85rem;
            line-height: 1.7;
        }

        .report-list-compact li {
            margin-bottom: 0.7rem;
        }

        .keyword-cloud {
            display: flex;
            flex-wrap: wrap;
            gap: 0.6rem;
        }

        .keyword-chip {
            display: inline-flex;
            align-items: center;
            padding: 0.5rem 0.8rem;
            border-radius: 999px;
            background: rgba(103,232,249,0.10);
            border: 1px solid rgba(103,232,249,0.18);
            color: #e9f7ff;
            font-size: 0.92rem;
            line-height: 1.2;
        }

        .empty-card {
            padding: 1rem 1.1rem;
            border-radius: 18px;
            background: rgba(15,23,42,0.56);
            border: 1px dashed rgba(148,163,184,0.18);
            color: #b9c8dc;
        }

        div[data-testid="metric-container"] {
            background:
                linear-gradient(180deg, rgba(10,18,35,0.88), rgba(15,23,42,0.74)),
                radial-gradient(circle at top right, rgba(103,232,249,0.10), transparent 35%);
            border: 1px solid rgba(148,163,184,0.12);
            padding: 1rem 1rem;
            border-radius: 22px;
            box-shadow: 0 18px 44px rgba(0,0,0,0.22);
        }

        div[data-testid="metric-container"] [data-testid="stMetricValue"] {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 3rem;
            color: #f8fbff;
        }

        div[data-testid="metric-container"] [data-testid="stMetricDelta"] {
            background: rgba(34,197,94,0.16);
            padding: 0.2rem 0.55rem;
            border-radius: 999px;
            width: fit-content;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.55rem;
            margin-bottom: 0.75rem;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 999px;
            padding: 0.25rem 1rem;
            background: rgba(15,23,42,0.65);
            border: 1px solid rgba(148,163,184,0.12);
            color: #b9c8dc;
            font-weight: 700;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #8b5cf6 0%, #2563eb 100%) !important;
            color: white !important;
        }

        .stDownloadButton > button,
        .stButton > button {
            border-radius: 999px;
            font-weight: 800;
        }

        .stDownloadButton > button {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #f8fbff;
            border: 1px solid rgba(148,163,184,0.18);
        }

        .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
            color: #f8fbff !important;
        }

        .stMarkdown p, .stMarkdown li {
            line-height: 1.7;
        }

        @media (max-width: 900px) {
            .hero-grid {
                grid-template-columns: 1fr;
            }

            .hero-signal {
                justify-self: start;
            }

            .space-orbit,
            .space-orbit-two,
            .space-orbit-three,
            .space-orbit-four,
            .shooting-star,
            .shooting-star-two,
            .shooting-star-three,
            .shooting-star-four,
            .space-grid {
                opacity: 0.55;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_background_fx():
    st.markdown(
        """
        <div class="space-layer" aria-hidden="true">
            <div class="space-nebula"></div>
            <div class="space-nebula-two"></div>
            <div class="space-nebula-three"></div>
            <div class="space-grid"></div>
            <div class="space-orbit">
                <div class="space-planet"></div>
            </div>
            <div class="space-orbit-two">
                <div class="space-planet-two"></div>
            </div>
            <div class="space-orbit-three">
                <div class="space-planet-three"></div>
            </div>
            <div class="space-orbit-four"></div>
            <div class="shooting-star"></div>
            <div class="shooting-star-two"></div>
            <div class="shooting-star-three"></div>
            <div class="shooting-star-four"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero(scores):
    lead_score = scores["Resume Score"] if scores else "--"
    lead_text = score_summary(scores["Resume Score"]) if scores else "Ready when you are"
    st.markdown(
        f"""
        <div class="hero-card">
            <div class="hero-grid">
                <div>
                    <div class="hero-kicker">Deep Space Scan</div>
                    <div class="hero-title"> AI RESUME Analyzer.Pro</div>
                    <p class="hero-copy">Drop in a resume, target the role, and turn the result into a dramatic ATS report with polished rewrites and high-contrast analytics.</p>
                </div>
                <div class="hero-signal">
                    <div class="hero-signal-label">Primary Signal</div>
                    <div class="hero-signal-score">{lead_score}</div>
                    <div class="hero-signal-note">{lead_text} overall momentum across your resume quality signal.</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metrics(scores):
    if not scores:
        return

    notes = [
        "Overall quality and readability",
        "Keyword and parser compatibility",
        "Role-fit strength",
    ]
    cols = st.columns(3)
    for col, (label, value), note in zip(cols, scores.items(), notes):
        with col:
            st.metric(label, value, score_summary(value))
            st.caption(note)


def glass_card(title, body):
    st.markdown(
        f"""
        <div class="glass-card">
            <div class="panel-title">{title}</div>
            <div class="panel-copy">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def empty_state(message):
    st.markdown(f'<div class="empty-card">{message}</div>', unsafe_allow_html=True)
