"""
Student Placement Intelligence Platform — Streamlit MVP
Run locally with:
    pip install -r requirements.txt
    streamlit run app.py
"""
import sys
import os
import tempfile
import pandas as pd
import streamlit as st

sys.path.append(os.path.join(os.path.dirname(__file__), "nlp"))
sys.path.append(os.path.join(os.path.dirname(__file__), "ml"))
from resume_parser import parse_resume, extract_text_from_file, load_skill_list  # noqa: E402
from engine import readiness_score, check_eligibility, interview_roadmap, companies_df  # noqa: E402

st.set_page_config(page_title="Placement Intelligence Platform", layout="wide")
st.title("🎓 Student Placement Intelligence Platform")
st.caption("Resume Analysis • Skill-Gap Analysis • Readiness Score • Company Eligibility • Interview Roadmap")

# ---------------- Sidebar: Input ----------------
st.sidebar.header("Your Profile")
input_mode = st.sidebar.radio("How do you want to provide your info?",
                               ["Upload resume", "Paste resume text", "Manual entry"])

skills, cgpa_guess = [], None

if input_mode == "Upload resume":
    file = st.sidebar.file_uploader("Upload resume (pdf/docx/txt)", type=["pdf", "docx", "txt"])
    if file:
        with tempfile.NamedTemporaryFile(delete=False, suffix="." + file.name.split(".")[-1]) as tmp:
            tmp.write(file.read())
            tmp_path = tmp.name
        text = extract_text_from_file(tmp_path)
        parsed = parse_resume(text)
        skills = parsed["skills"]
        cgpa_guess = parsed["cgpa"]
        st.sidebar.success(f"Extracted {len(skills)} skills from resume.")

elif input_mode == "Paste resume text":
    text = st.sidebar.text_area("Paste resume text here", height=200)
    if text:
        parsed = parse_resume(text)
        skills = parsed["skills"]
        cgpa_guess = parsed["cgpa"]

all_skills = load_skill_list()
skills = st.sidebar.multiselect("Skills (edit/confirm)", options=all_skills, default=skills)

branch = st.sidebar.selectbox("Branch", ["CSE", "IT", "ECE", "EEE", "MECH", "CIVIL"])
cgpa = st.sidebar.number_input("CGPA", 0.0, 10.0, value=float(cgpa_guess) if cgpa_guess else 7.0, step=0.1)
backlogs = st.sidebar.number_input("Active Backlogs", 0, 10, 0)
projects = st.sidebar.number_input("Number of Projects", 0, 20, 2)
internships = st.sidebar.number_input("Number of Internships", 0, 10, 0)
certifications = st.sidebar.number_input("Number of Certifications", 0, 20, 1)
communication_score = st.sidebar.slider("Self-rated Communication Skill (1-10)", 1, 10, 6)

student = {
    "branch": branch, "cgpa": cgpa, "backlogs": backlogs, "skills": skills,
    "projects": projects, "internships": internships,
    "certifications": certifications, "communication_score": communication_score,
}

# ---------------- Main: Results ----------------
if not skills:
    st.info("Add your skills in the sidebar (or upload/paste a resume) to see your full report.")
    st.stop()

score = readiness_score(cgpa, backlogs, len(skills), projects, internships, certifications, communication_score)

col1, col2, col3 = st.columns(3)
col1.metric("Placement Readiness Score", f"{score}/100")
band = "🟢 High" if score >= 70 else "🟡 Medium" if score >= 40 else "🔴 Low"
col2.metric("Readiness Band", band)
col3.metric("Skills Identified", len(skills))

st.divider()

st.subheader("🏢 Company-wise Eligibility Checker")
eligibility = check_eligibility(student, companies_df)
elig_df = pd.DataFrame(eligibility)
elig_df["missing_skills"] = elig_df["missing_skills"].apply(lambda x: ", ".join(x) if x else "—")
st.dataframe(
    elig_df[["company", "role", "package_lpa", "eligible", "skill_match_pct", "missing_skills"]],
    use_container_width=True, hide_index=True
)

st.subheader("📊 Skill Gap Analysis")
top_target = eligibility[0]
st.write(f"Closest target right now: **{top_target['company']}** ({top_target['skill_match_pct']}% match)")
missing_all = sorted(set(s for e in eligibility if not e["eligible"] for s in e["missing_skills"]))
if missing_all:
    st.bar_chart(pd.Series(missing_all).value_counts() if len(missing_all) != len(set(missing_all))
                 else pd.Series([1] * len(missing_all), index=missing_all))
else:
    st.success("No skill gaps for eligible companies — you're matching well!")

st.subheader("🗺️ Interview Preparation Roadmap")
priority_missing = [e["missing_skills"] for e in eligibility if not e["eligible"]]
flat_missing = [s for sub in priority_missing for s in sub]
freq = pd.Series(flat_missing).value_counts().index.tolist() if flat_missing else []
roadmap = interview_roadmap(freq)
for r in roadmap:
    st.markdown(f"- **{r['skill']}**: {r['recommendation']}")
if not roadmap:
    st.success("You're eligible for your top targets with no major skill gaps. Focus on mock interviews!")
