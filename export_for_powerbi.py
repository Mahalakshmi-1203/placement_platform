"""
Scores every student in students.csv, runs the eligibility checker against
every company, and writes flat CSVs designed to be imported straight into
Power BI (Get Data > Text/CSV), with a ready-made star-schema relationship.

Run: python3 export_for_powerbi.py
Outputs (in this folder):
  fact_eligibility.csv     - one row per student x company (the core fact table)
  dim_students.csv         - one row per student (with readiness_score)
  dim_companies.csv        - one row per company
  skill_gap_summary.csv    - most in-demand missing skills, for a bar chart
"""
import os
import sys
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "ml"))
from engine import readiness_score, check_eligibility  # noqa: E402

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "..", "data")

students_df = pd.read_csv(os.path.join(DATA, "students.csv"))
companies_df = pd.read_csv(os.path.join(DATA, "companies.csv"))

student_rows = []
fact_rows = []
all_missing = []

for _, s in students_df.iterrows():
    skills = s["skills"].split(";")
    score = readiness_score(
        s["cgpa"], s["backlogs"], len(skills),
        s["projects"], s["internships"], s["certifications"], s["communication_score"]
    )
    student = {"branch": s["branch"], "cgpa": s["cgpa"], "backlogs": s["backlogs"], "skills": skills}
    elig_results = check_eligibility(student, companies_df)

    for e in elig_results:
        fact_rows.append({
            "student_id": s["student_id"],
            "company": e["company"],
            "role": e["role"],
            "package_lpa": e["package_lpa"],
            "eligible": int(e["eligible"]),
            "skill_match_pct": e["skill_match_pct"],
            "missing_skills": ", ".join(e["missing_skills"]),
        })
        if not e["eligible"]:
            all_missing.extend(e["missing_skills"])

    student_rows.append({
        "student_id": s["student_id"],
        "name": s["name"],
        "branch": s["branch"],
        "cgpa": s["cgpa"],
        "backlogs": s["backlogs"],
        "num_skills": len(skills),
        "projects": s["projects"],
        "internships": s["internships"],
        "certifications": s["certifications"],
        "readiness_score": score,
        "readiness_band": (
            "High" if score >= 70 else "Medium" if score >= 40 else "Low"
        ),
        "historically_placed": s["placed"],
    })

pd.DataFrame(student_rows).to_csv(os.path.join(BASE, "dim_students.csv"), index=False)
companies_df.rename(columns={"company": "company"}).to_csv(
    os.path.join(BASE, "dim_companies.csv"), index=False
)
pd.DataFrame(fact_rows).to_csv(os.path.join(BASE, "fact_eligibility.csv"), index=False)

skill_gap_summary = (
    pd.Series(all_missing)
    .value_counts()
    .reset_index()
)
skill_gap_summary.columns = ["missing_skill", "students_affected"]
skill_gap_summary.to_csv(os.path.join(BASE, "skill_gap_summary.csv"), index=False)

print("Exported:")
for fname in ["dim_students.csv", "dim_companies.csv", "fact_eligibility.csv", "skill_gap_summary.csv"]:
    path = os.path.join(BASE, fname)
    print(f"  {fname:25s} -> {sum(1 for _ in open(path)) - 1} rows")
