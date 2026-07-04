# 🎓 Student Placement Intelligence Platform — MVP

Helps engineering students answer: *Am I placement-ready? What am I
missing? Which companies can I target?*

## Features (this MVP)
1. **Resume Analyzer** (NLP) — extracts skills, CGPA, projects, internships, certifications from a resume (pdf/docx/txt/pasted text).
2. **Skill-Gap Analysis** — compares a student's skills against each company's required skill set.
3. **Placement Readiness Score** (ML) — a Logistic Regression model trained on CGPA, backlogs, skill count, projects, internships, certifications, and communication score, output as a 0–100 score.
4. **Company-wise Eligibility Checker** — filters companies by CGPA cutoff, backlog limit, branch, and skill-match threshold.
5. **Power BI Dashboard** — pre-shaped CSV exports + a full build guide (KPIs, DAX measures, page layouts).

## Architecture
```
placement_platform/
├── data/
│   ├── skills_master.csv       # 50 skills, categorized
│   ├── companies.csv           # 20 companies w/ eligibility criteria + required skills
│   ├── generate_data.py        # synthetic student dataset generator
│   └── students.csv            # 400 synthetic student records (generated)
├── db/
│   ├── schema.sql              # normalized SQL schema (students, skills, companies, eligibility_results)
│   ├── build_db.py             # loads CSVs into SQLite (placement.db)
│   └── placement.db            # generated SQLite database
├── nlp/
│   └── resume_parser.py        # rule-based resume parsing (skills, CGPA, experience signals)
├── ml/
│   ├── train_model.py          # trains + evaluates the readiness-score model
│   ├── readiness_model.pkl     # trained sklearn pipeline
│   ├── model_weights.json      # portable weights (used by engine.py, and by the JS demo)
│   └── engine.py                # core logic: readiness score, skill gap, eligibility, roadmap
├── powerbi/
│   ├── export_for_powerbi.py   # scores all students + exports Power-BI-ready CSVs
│   ├── dim_students.csv / dim_companies.csv / fact_eligibility.csv / skill_gap_summary.csv
│   └── README_PowerBI.md       # step-by-step dashboard build guide
├── app.py                      # Streamlit MVP web app (all 5 features together)
└── requirements.txt
```

## How to run locally
```bash
pip install -r requirements.txt

# 1. Regenerate data (optional — students.csv is already included)
cd data && python3 generate_data.py && cd ..

# 2. Build the SQL database
cd db && python3 build_db.py && cd ..

# 3. Train the ML model
cd ml && python3 train_model.py && python3 engine.py && cd ..

# 4. Export Power BI data
cd powerbi && python3 export_for_powerbi.py && cd ..

# 5. Launch the app
streamlit run app.py
```

## Model performance (on synthetic data)
ROC-AUC ≈ 0.98, accuracy ≈ 95% — strong signal on synthetic data. **Before using
this for real students, retrain `train_model.py` on real historical placement
data from your college's placement cell** (same CSV shape as `students.csv`);
synthetic-data performance won't transfer 1:1 to real-world noise.

## Extending this MVP
- Swap `resume_parser.py`'s keyword matching for spaCy NER / a fine-tuned
  transformer for more robust entity extraction.
- Replace Logistic Regression with a Gradient Boosted model (XGBoost/LightGBM)
  once you have a larger real dataset — keep `model_weights.json` export logic
  if you want a portable JS/no-server version of the scorer.
- Add authentication + a real backend (FastAPI + Postgres) if this needs to
  scale beyond a single-college pilot.
- Add a resume "improvement suggestions" module using an LLM (e.g. Claude API)
  fed with the parsed resume + missing skills.
