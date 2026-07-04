"""
Placement Intelligence Engine
-----------------------------
Combines the resume parser output with company data to produce:
  1. Placement readiness score (ML model)
  2. Skill-gap analysis per target company
  3. Company-wise eligibility checker
  4. A simple interview-prep roadmap based on missing skills

Run: python3 engine.py   (uses a sample student profile)
"""
import os
import json
import math
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "..", "data")

companies_df = pd.read_csv(os.path.join(DATA, "companies.csv"))
with open(os.path.join(BASE, "model_weights.json")) as f:
    WEIGHTS = json.load(f)

ROADMAP_RESOURCES = {
    "Data Structures": "Practice arrays/trees/graphs daily on LeetCode/GFG (4-6 weeks).",
    "Algorithms": "Master sorting, searching, DP, greedy via a structured DSA sheet.",
    "SQL": "Do 50+ SQL practice problems (joins, window functions) on HackerRank/LeetCode.",
    "System Design": "Study basics: scalability, load balancing, caching; follow 'Grokking System Design'.",
    "Java": "Build 2 mini projects in Java; revise OOP concepts thoroughly.",
    "Python": "Complete a Python DSA course + build 1-2 automation/ML projects.",
    "Machine Learning": "Complete Andrew Ng's ML course; build 2 end-to-end ML projects.",
    "Power BI": "Build 2 dashboards using real datasets (Kaggle) with DAX measures.",
    "Communication Skills": "Do 5 mock interviews; practice structured answers (STAR method).",
    "Statistics": "Revise probability, hypothesis testing, regression basics.",
    "Data Analysis": "Practice EDA on 3 real-world datasets using Pandas.",
    "Git": "Learn branching, PRs, and push 3 personal projects to GitHub.",
    "Operating Systems": "Revise process scheduling, memory management, deadlocks.",
    "Computer Networks": "Revise OSI/TCP-IP model, common interview Qs.",
    "REST API": "Build and consume a REST API using Flask/Express.",
}
DEFAULT_TIP = "Take an online course + build one small project to demonstrate this skill."


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


def readiness_score(cgpa, backlogs, num_skills, projects, internships, certifications, communication_score):
    """Reproduces the trained Logistic Regression using exported weights,
    so this can run without loading the pickled sklearn model."""
    raw = {
        "cgpa": cgpa, "backlogs": backlogs, "num_skills": num_skills,
        "projects": projects, "internships": internships,
        "certifications": certifications, "communication_score": communication_score,
    }
    z = WEIGHTS["intercept"]
    for i, feat in enumerate(WEIGHTS["features"]):
        x = raw[feat]
        mean = WEIGHTS["mean"][i]
        scale = WEIGHTS["scale"][i]
        z += WEIGHTS["coef"][i] * ((x - mean) / scale)
    return round(sigmoid(z) * 100, 1)


def skill_gap(student_skills, required_skills):
    student_set = set(s.strip().lower() for s in student_skills)
    required_set = [s.strip() for s in required_skills]
    missing = [s for s in required_set if s.lower() not in student_set]
    matched = [s for s in required_set if s.lower() in student_set]
    pct = round(100 * len(matched) / len(required_set), 1) if required_set else 100.0
    return {"matched": matched, "missing": missing, "match_pct": pct}


def check_eligibility(student, companies=companies_df):
    """student: dict with cgpa, backlogs, branch, skills(list)"""
    results = []
    for _, c in companies.iterrows():
        required_skills = [s.strip() for s in c["required_skills"].split(",")]
        gap = skill_gap(student["skills"], required_skills)

        branch_ok = (c["branches_allowed"] == "All") or (student["branch"] in c["branches_allowed"].split("/"))
        cgpa_ok = student["cgpa"] >= c["min_cgpa"]
        backlog_ok = student["backlogs"] <= c["max_backlogs"]

        eligible = branch_ok and cgpa_ok and backlog_ok and gap["match_pct"] >= 40

        results.append({
            "company": c["company"],
            "role": c["role"],
            "package_lpa": c["package_lpa"],
            "eligible": eligible,
            "cgpa_ok": cgpa_ok,
            "backlog_ok": backlog_ok,
            "branch_ok": branch_ok,
            "skill_match_pct": gap["match_pct"],
            "missing_skills": gap["missing"],
        })
    return sorted(results, key=lambda r: (-r["eligible"], -r["skill_match_pct"]))


def interview_roadmap(missing_skills, top_n=5):
    roadmap = []
    for skill in missing_skills[:top_n]:
        roadmap.append({
            "skill": skill,
            "recommendation": ROADMAP_RESOURCES.get(skill, DEFAULT_TIP)
        })
    return roadmap


def full_report(student):
    """student: {name, branch, cgpa, backlogs, skills, projects, internships, certifications, communication_score}"""
    score = readiness_score(
        student["cgpa"], student["backlogs"], len(student["skills"]),
        student["projects"], student["internships"],
        student["certifications"], student["communication_score"]
    )
    eligibility = check_eligibility(student)
    top_target = eligibility[0] if eligibility else None
    all_missing = []
    for e in eligibility:
        all_missing.extend(e["missing_skills"])
    # rank missing skills by frequency across companies (most valuable to learn first)
    freq = pd.Series(all_missing).value_counts()
    priority_missing = freq.index.tolist()

    return {
        "readiness_score": score,
        "eligibility": eligibility,
        "top_recommendation": top_target,
        "roadmap": interview_roadmap(priority_missing),
    }


if __name__ == "__main__":
    sample_student = {
        "name": "Aditya Sharma",
        "branch": "CSE",
        "cgpa": 7.8,
        "backlogs": 0,
        "skills": ["Python", "Java", "Data Structures", "SQL", "Git"],
        "projects": 2,
        "internships": 1,
        "certifications": 1,
        "communication_score": 6,
    }
    report = full_report(sample_student)
    print("Readiness Score:", report["readiness_score"])
    print("\nTop 5 eligible companies:")
    for e in report["eligibility"][:5]:
        print(f"  {e['company']:15s} eligible={e['eligible']!s:5} match={e['skill_match_pct']}%  missing={e['missing_skills']}")
    print("\nInterview Prep Roadmap:")
    for r in report["roadmap"]:
        print(f"  - {r['skill']}: {r['recommendation']}")
