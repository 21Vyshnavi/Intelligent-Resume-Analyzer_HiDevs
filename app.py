"""
app.py  –  Streamlit UI for Intelligent Resume Analyzer
Run with:  streamlit run app.py
"""

import json
import sys
from pathlib import Path

import streamlit as st

# Make src importable when running from project root
sys.path.insert(0, str(Path(__file__).parent))

from src.resume_parser import ResumeParser
from src.matcher import ResumeMatcher
from src.report_generator import ReportGenerator
from src.file_handler import (
    save_candidate,
    list_candidates,
    load_candidate,
    OUTPUT_DIR,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Intelligent Resume Analyzer",
    page_icon="📄",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.title("⚙️ Job Requirements")

job_title = st.sidebar.text_input("Job Title", placeholder="e.g. Senior Python Developer")
company   = st.sidebar.text_input("Company", placeholder="e.g. TechCorp India")

st.sidebar.subheader("Required Skills")
skills_input = st.sidebar.text_area(
    "Enter skills (one per line or comma-separated)",
    placeholder="Python\nDjango\nPostgreSQL\nDocker",
    height=140,
)

min_exp = st.sidebar.slider("Minimum Experience (years)", 0, 15, 2)
req_degree = st.sidebar.selectbox(
    "Minimum Degree",
    ["Any", "Diploma", "B.Tech / B.E", "M.Tech / M.E", "MBA", "Ph.D"],
)

st.sidebar.divider()
st.sidebar.subheader("📂 Saved Candidates")
if st.sidebar.button("Refresh List"):
    st.rerun()

saved = list_candidates()
if saved:
    for rec in saved:
        score = rec["overall_score"]
        color = "🟢" if score >= 76 else "🟡" if score >= 50 else "🔴"
        st.sidebar.markdown(
            f"{color} **{rec['name']}** — {score:.0f}/100  \n"
            f"_{rec['verdict']}_"
        )
else:
    st.sidebar.caption("No candidates saved yet.")

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
st.title("📄 Intelligent Resume Analyzer")
st.caption("Paste a resume, set job requirements in the sidebar, and get a complete AI-powered hiring report.")

tab_analyze, tab_history, tab_compare = st.tabs(
    ["🔍 Analyze Resume", "📋 History", "⚖️ Compare Candidates"]
)

# ====================================================
# TAB 1 – Analyze
# ====================================================
with tab_analyze:
    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("Resume Text")
        resume_text = st.text_area(
            "Paste the candidate's resume here",
            height=380,
            placeholder="John Doe\njohn.doe@email.com\n\nExperience:\n...",
            label_visibility="collapsed",
        )

        jd_text = st.text_area(
            "Job Description (optional – paste full JD for better skill matching)",
            height=120,
            placeholder="We are looking for a Python developer with experience in Django and PostgreSQL...",
        )

    with col2:
        st.subheader("Sample Resumes")
        samples = {
            "Priya Sharma – Full Stack Dev": (
                "Name: Priya Sharma\nEmail: priya.sharma@email.com\nPhone: +91-9876543210\n\n"
                "Summary:\nFull-stack developer with 4 years of experience building scalable web applications.\n\n"
                "Experience:\n- Software Engineer at TechCorp (2021-2025): Built REST APIs in Python/Django, React dashboards, PostgreSQL.\n"
                "- Junior Developer at StartupXYZ (2020-2021): Node.js and Vue.js.\n\n"
                "Skills: Python, Django, React, JavaScript, PostgreSQL, Docker, Git, REST API, Redis, AWS\n\n"
                "Education:\nB.Tech Computer Science, IIT Hyderabad, 2020"
            ),
            "Rahul Verma – Data Scientist": (
                "Name: Rahul Verma\nEmail: rahul.verma@email.com\nPhone: +91-8765432109\n\n"
                "Summary:\nData Scientist with 3 years building ML models and data pipelines.\n\n"
                "Experience:\n- Data Scientist at Analytics Co (2022-2025): NLP models, scikit-learn, AWS SageMaker.\n"
                "- Data Analyst at DataHub (2021-2022): SQL, Tableau.\n\n"
                "Skills: Python, Machine Learning, scikit-learn, TensorFlow, SQL, Pandas, NumPy, AWS, Tableau, NLP\n\n"
                "Education:\nM.Sc Data Science, IISc Bangalore, 2021\n\nCertifications: AWS Certified ML Specialist"
            ),
            "Anita Roy – DevOps Engineer": (
                "Name: Anita Roy\nEmail: anita.roy@email.com\nPhone: +91-7654321098\n\n"
                "Summary:\nDevOps Engineer with 5 years automating infrastructure and CI/CD pipelines.\n\n"
                "Experience:\n- Senior DevOps Engineer at CloudSoft (2020-2025): Kubernetes, Jenkins, Terraform. Reduced deploy time 60%.\n"
                "- Systems Engineer at Infosys (2018-2020): Linux, shell scripting, Prometheus/Grafana.\n\n"
                "Skills: Kubernetes, Docker, Jenkins, Terraform, AWS, Linux, Python, GitHub Actions, Prometheus, Grafana, Ansible\n\n"
                "Education:\nB.E Electronics, Anna University, 2018"
            ),
        }

        selected_sample = st.selectbox("Load a sample", ["— select —"] + list(samples.keys()))
        if selected_sample != "— select —":
            st.session_state["loaded_resume"] = samples[selected_sample]
            st.info("Sample loaded — switch to the text area and it will appear on next rerun.")

        if "loaded_resume" in st.session_state and not resume_text:
            resume_text = st.session_state["loaded_resume"]

    # --- Analyze button ---
    if st.button("🔍  Analyze Resume", type="primary", use_container_width=True):
        if not resume_text.strip():
            st.error("Please paste a resume before analyzing.")
        else:
            with st.spinner("Parsing and matching…"):
                try:
                    # 1. Parse
                    parser    = ResumeParser(resume_text)
                    candidate = parser.parse()

                    # 2. Skills from sidebar
                    required_skills = []
                    if skills_input.strip():
                        raw = skills_input.replace(",", "\n")
                        required_skills = [s.strip() for s in raw.splitlines() if s.strip()]

                    # 3. Degree mapping
                    degree_map = {
                        "Any": "", "Diploma": "diploma",
                        "B.Tech / B.E": "b.tech", "M.Tech / M.E": "m.tech",
                        "MBA": "mba", "Ph.D": "phd",
                    }

                    # 4. Match
                    matcher = ResumeMatcher(
                        candidate=candidate,
                        required_skills=required_skills,
                        job_description=jd_text,
                        min_experience_years=min_exp,
                        required_degree=degree_map.get(req_degree, ""),
                    )
                    match_result = matcher.match()

                    # 5. Report
                    reporter = ReportGenerator(
                        candidate=candidate,
                        match=match_result,
                        job_title=job_title or "the position",
                        company=company,
                    )

                    # 6. Save to JSON
                    saved_path = save_candidate(candidate, match_result)

                    # --------------- Results UI ---------------
                    st.divider()
                    st.subheader("📊 Analysis Results")

                    score = match_result["overall_score"]
                    verdict = match_result["verdict"]
                    color = "green" if score >= 76 else "orange" if score >= 50 else "red"

                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Overall Score", f"{score:.0f} / 100")
                    c2.metric("Skill Match",   f"{match_result['skill_score']:.0f}")
                    c3.metric("Experience",    f"{match_result['experience_score']:.0f}")
                    c4.metric("Education",     f"{match_result['education_score']:.0f}")

                    st.markdown(f"**Verdict:** :{color}[{verdict}]")
                    st.progress(int(score))
                    st.info(match_result.get("recommendation", ""))

                    st.divider()
                    col_left, col_right = st.columns(2)

                    with col_left:
                        st.subheader("👤 Candidate")
                        st.write(f"**Name:** {candidate.get('name','N/A')}")
                        st.write(f"**Email:** {candidate.get('email','N/A')}")
                        st.write(f"**Phone:** {candidate.get('phone','N/A')}")
                        st.write(f"**Experience:** {candidate.get('total_experience_years',0)} years")
                        edu = candidate.get("education", [])
                        if edu:
                            st.write(f"**Education:** {edu[0].get('degree','')} {edu[0].get('year','')}")
                        if candidate.get("summary"):
                            st.caption(candidate["summary"])

                    with col_right:
                        st.subheader("🛠️ Skills")
                        matched = match_result.get("matched_skills", [])
                        missing = match_result.get("missing_skills", [])
                        all_sk  = candidate.get("skills", [])

                        if matched:
                            st.markdown("**✅ Matched:**  " + "  ".join(f"`{s}`" for s in matched))
                        if missing:
                            st.markdown("**❌ Missing:**  " + "  ".join(f"`{s}`" for s in missing))
                        if all_sk:
                            st.markdown("**All extracted:**  " + "  ".join(f"`{s}`" for s in all_sk))

                    st.divider()
                    st.subheader("📄 Full Report")

                    report_text = reporter.generate_text()
                    report_md   = reporter.generate_markdown()

                    with st.expander("View text report"):
                        st.code(report_text, language=None)

                    dl1, dl2, dl3 = st.columns(3)
                    dl1.download_button(
                        "⬇️ Download TXT",
                        data=report_text,
                        file_name=f"report_{candidate.get('name','candidate').replace(' ','_')}.txt",
                        mime="text/plain",
                    )
                    dl2.download_button(
                        "⬇️ Download Markdown",
                        data=report_md,
                        file_name=f"report_{candidate.get('name','candidate').replace(' ','_')}.md",
                        mime="text/markdown",
                    )
                    dl3.download_button(
                        "⬇️ Download JSON",
                        data=json.dumps({"candidate": candidate, "match_result": match_result}, indent=2),
                        file_name=f"report_{candidate.get('name','candidate').replace(' ','_')}.json",
                        mime="application/json",
                    )

                    st.success(f"Analysis saved → `{saved_path}`")

                except ValueError as err:
                    st.error(f"Parsing error: {err}")
                except Exception as err:
                    st.error(f"Unexpected error: {err}")
                    raise

# ====================================================
# TAB 2 – History
# ====================================================
with tab_history:
    st.subheader("Saved Candidate Records")
    records = list_candidates()

    if not records:
        st.info("No records yet. Analyze a resume to get started.")
    else:
        for rec in records:
            score = rec["overall_score"]
            icon  = "🟢" if score >= 76 else "🟡" if score >= 50 else "🔴"
            with st.expander(f"{icon} {rec['name']}  –  {score:.0f}/100  |  {rec['verdict']}"):
                st.write(f"**Email:** {rec['email']}")
                st.write(f"**Analyzed at:** {rec['analyzed_at']}")
                st.write(f"**File:** `{rec['filepath']}`")
                if st.button("Load full record", key=rec["filepath"]):
                    full = load_candidate(rec["filepath"])
                    st.json(full)

# ====================================================
# TAB 3 – Compare
# ====================================================
with tab_compare:
    st.subheader("Compare Candidates Side by Side")
    records = list_candidates()

    if len(records) < 2:
        st.info("Analyze at least two resumes to enable comparison.")
    else:
        names   = [r["name"] for r in records]
        pick_a  = st.selectbox("Candidate A", names, key="cmp_a")
        pick_b  = st.selectbox("Candidate B", [n for n in names if n != pick_a], key="cmp_b")

        rec_a = next(r for r in records if r["name"] == pick_a)
        rec_b = next(r for r in records if r["name"] == pick_b)

        cols = st.columns(2)
        for col, rec in zip(cols, [rec_a, rec_b]):
            full = load_candidate(rec["filepath"])
            m    = full["match_result"]
            c    = full["candidate"]
            with col:
                st.markdown(f"### {rec['name']}")
                st.metric("Overall",    f"{m['overall_score']:.0f}")
                st.metric("Skills",     f"{m['skill_score']:.0f}")
                st.metric("Experience", f"{m['experience_score']:.0f}")
                st.metric("Education",  f"{m['education_score']:.0f}")
                st.write(f"**Verdict:** {m['verdict']}")
                st.caption(m.get("recommendation",""))
                if c.get("skills"):
                    st.markdown("**Skills:** " + ", ".join(c["skills"][:10]))
