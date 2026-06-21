import time

import streamlit as st

from frontend import empty_state, render_background_fx, render_hero, render_metrics, render_report_block, render_styles
from services.analysis_service import (
    analysis_json_to_legacy_format,
    analyze_resume,
    build_job_description_context,
    clean_resume_text,
    extract_keywords_from_analysis,
    generate_updated_resume,
    normalize_analysis_items,
    parse_scores,
    split_analysis_sections,
    strip_markdown_links,
)
from services.chart_service import create_gauge_chart, create_score_chart
from services.file_service import (
    clear_generated_outputs as _clear_generated_outputs,
    extract_text,
    generate_pdf_bytes,
    generate_resume_docx_bytes,
    get_uploaded_file_signature,
)
from services.groq_service import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    GROQ_CALL_COOLDOWN_SECONDS,
    GROQ_FALLBACK_MODEL,
    GROQ_MODEL,
    GROQ_REQUEST_TIMEOUT_SECONDS,
    call_groq_with_retry,
    classify_groq_error,
    format_groq_error_message,
    get_groq_client,
    get_groq_model_candidates,
    groq_call_allowed,
    is_model_unavailable_error,
    is_transient_groq_error,
    RateLimitError,
)


def init_session_state():
    defaults = {
        "analysis": None,
        "analysis_pdf": None,
        "improved_resume": None,
        "improved_resume_docx": None,
        "improved_resume_pdf": None,
        "scores": None,
        "last_uploaded_signature": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def reset_app():
    for key in [
        "analysis",
        "analysis_pdf",
        "improved_resume",
        "improved_resume_docx",
        "improved_resume_pdf",
        "scores",
        "last_uploaded_signature",
        "resume_uploader",
        "job_role_input",
        "chart_selector",
    ]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()


def clear_generated_outputs():
    _clear_generated_outputs(st)


def main():
    st.set_page_config(page_title="AI Resume Analyzer Pro", page_icon="A", layout="wide")
    init_session_state()
    render_styles()
    render_background_fx()
    client = get_groq_client()

    current_upload_signature = st.session_state.get("last_uploaded_signature")

    with st.sidebar:
        st.markdown("## Control Deck")
        st.caption("Upload a resume, set the role, then launch the scan.")
        resume_file = st.file_uploader("Resume File", type=["pdf", "docx"], key="resume_uploader")
        job_role = st.text_input(
            "Target Job Role",
            key="job_role_input",
            placeholder="Machine Learning Engineer — or paste a full job description",
        )
        chart_type = st.selectbox(
            "Visualization Type",
            ["Vertical Bar", "Horizontal Bar", "Pie Chart", "Radar Chart", "Gauge Dashboard"],
            key="chart_selector",
        )
        analyze_btn = st.button("Analyze Resume", type="primary", use_container_width=True)
        reset_btn = st.button("Reset", use_container_width=True)

    if reset_btn:
        reset_app()

    current_signature = None
    if resume_file:
        current_signature = get_uploaded_file_signature(resume_file)
        if current_signature != current_upload_signature:
            clear_generated_outputs()
            st.session_state["last_uploaded_signature"] = current_signature

    if analyze_btn:
        if not resume_file:
            st.warning("Please upload a resume.")
        elif not groq_call_allowed("shared"):
            pass
        else:
            try:
                with st.spinner("Analyzing resume..."):
                    resume_text = extract_text(resume_file)
                    if not resume_text:
                        st.warning("We couldn't extract any text from that file. Please upload a text-based PDF or DOCX.")
                    else:
                        analysis_result = analyze_resume(client, resume_text, job_role or "General role")
                        st.session_state["analysis"] = analysis_result["analysis"]
                        st.session_state["scores"] = analysis_result["scores"]
                        st.session_state["analysis_pdf"] = generate_pdf_bytes(analysis_result["analysis"])
                        st.session_state["improved_resume"] = None
                        st.session_state["improved_resume_docx"] = None
                        st.session_state["improved_resume_pdf"] = None
            except Exception as exc:
                clear_generated_outputs()
                st.error(format_groq_error_message(exc))

    render_hero(st.session_state["scores"])
    render_metrics(st.session_state["scores"])

    tab1, tab2, tab3 = st.tabs(["Analysis", "Visuals", "Improved Resume"])

    with tab1:
        st.subheader("Resume Analysis")
        if st.session_state["analysis"]:
            sections = split_analysis_sections(st.session_state["analysis"])
            render_report_block("Top Suggestions", sections["top_suggestions"], variant="list")
            render_report_block("Missing Keywords", sections["missing_keywords"], variant="keywords")
            render_report_block("Skill Gap Analysis", sections["skill_gap_analysis"], variant="insights")
            render_report_block("Improved Bullet Points", sections["improved_bullets"], variant="list")

            if sections["other_notes"]:
                render_report_block("Additional Notes", sections["other_notes"], variant="insights")

            st.download_button(
                "Download Analysis Report",
                st.session_state["analysis_pdf"],
                file_name="resume_analysis_report.pdf",
                mime="application/pdf",
            )
        else:
            empty_state("Run the analysis to see the recruiter-style report here.")

    with tab2:
        st.subheader("Visual Analytics")
        if st.session_state["scores"]:
            if chart_type == "Gauge Dashboard":
                figure = create_gauge_chart(st.session_state["scores"])
            else:
                figure = create_score_chart(st.session_state["scores"], chart_type)
            st.plotly_chart(figure, use_container_width=True)
        else:
            empty_state("Charts will appear here after analysis.")

    with tab3:
        st.subheader("Improved Resume")
        generate_improved = st.button("Generate Improved Resume")

        if generate_improved:
            if not resume_file:
                st.warning("Please upload a resume first.")
            elif not groq_call_allowed("shared"):
                pass
            else:
                try:
                    with st.spinner("Generating improved resume..."):
                        resume_text = extract_text(resume_file)
                        if not resume_text:
                            st.warning("We couldn't extract any text from that file. Please upload a text-based PDF or DOCX.")
                        else:
                            improved_resume_raw = generate_updated_resume(client, resume_text)
                            improved_resume = clean_resume_text(improved_resume_raw)
                            st.session_state["improved_resume"] = improved_resume
                            st.session_state["improved_resume_docx"] = generate_resume_docx_bytes(improved_resume)
                            st.session_state["improved_resume_pdf"] = generate_pdf_bytes(improved_resume)
                except Exception as exc:
                    st.session_state["improved_resume"] = None
                    st.session_state["improved_resume_docx"] = None
                    st.session_state["improved_resume_pdf"] = None
                    st.error(format_groq_error_message(exc))

        if st.session_state["improved_resume"]:
            st.text_area("Clean Resume Output", st.session_state["improved_resume"], height=520)
            download_col1, download_col2, download_col3 = st.columns(3)
            with download_col1:
                st.download_button(
                    "Download PDF",
                    st.session_state["improved_resume_pdf"],
                    file_name="improved_resume.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            with download_col2:
                st.download_button(
                    "Download DOCX",
                    st.session_state["improved_resume_docx"],
                    file_name="improved_resume.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )
            with download_col3:
                st.download_button(
                    "Download TXT",
                    st.session_state["improved_resume"],
                    file_name="improved_resume.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
        else:
            empty_state("Generate an improved version of the uploaded resume here.")


if __name__ == "__main__":
    main()
