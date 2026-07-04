# Power BI Dashboard — Build Guide

This folder contains 4 CSVs already shaped for Power BI. Import them and
follow the steps below to get a working placement-intelligence dashboard
in ~20 minutes.

## 1. Import data
Power BI Desktop → **Get Data → Text/CSV** → import all four files:
- `dim_students.csv` — one row per student, with `readiness_score` and `readiness_band`
- `dim_companies.csv` — one row per company, with eligibility criteria
- `fact_eligibility.csv` — one row per (student, company) pair — the core fact table
- `skill_gap_summary.csv` — most commonly missing skills across all students

## 2. Build the data model
Go to **Model view** and create relationships:
- `dim_students[student_id]` **1 → \*** `fact_eligibility[student_id]`
- `dim_companies[company]` **1 → \*** `fact_eligibility[company]`

## 3. Suggested measures (DAX)
```DAX
Total Students = DISTINCTCOUNT(dim_students[student_id])

Placement Ready % =
DIVIDE(
    CALCULATE(COUNTROWS(dim_students), dim_students[readiness_band] = "High"),
    [Total Students]
)

Avg Readiness Score = AVERAGE(dim_students[readiness_score])

Eligible Company Matches =
CALCULATE(COUNTROWS(fact_eligibility), fact_eligibility[eligible] = 1)

Avg Skill Match % = AVERAGE(fact_eligibility[skill_match_pct])
```

## 4. Suggested visuals (pages)

**Page 1 — Placement Readiness Overview**
- KPI cards: Total Students, Placement Ready %, Avg Readiness Score
- Histogram: `readiness_score` distribution
- Donut chart: `readiness_band` (High/Medium/Low) split
- Bar chart: Avg Readiness Score by `branch`

**Page 2 — Skill Gap Analysis**
- Bar chart: `skill_gap_summary` — missing_skill vs students_affected (sorted desc)
- Matrix: branch x top missing skill
- Card: most in-demand missing skill

**Page 3 — Company Eligibility Explorer**
- Slicer: company, branch, readiness_band
- Table: student name, company, eligible (Yes/No), skill_match_pct, missing_skills
- Bar chart: number of eligible students per company
- Scatter: package_lpa vs Avg Skill Match % per company

**Page 4 — Individual Student Drilldown**
- Slicer: student name
- Card: readiness_score, cgpa, num_skills
- Table: eligible companies for the selected student, sorted by skill_match_pct

## 5. Refreshing with real data later
Re-run `export_for_powerbi.py` after replacing `students.csv` with real
(anonymized) placement-cell data — the CSV shape stays identical, so you
can just hit **Refresh** in Power BI.
