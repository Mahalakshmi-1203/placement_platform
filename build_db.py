"""
Builds placement.db (SQLite) from the CSV data + schema.sql.
Run from the db/ folder: python3 build_db.py
"""
import sqlite3
import pandas as pd
import os

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "..", "data")
DB_PATH = os.path.join(BASE, "placement.db")

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

with open(os.path.join(BASE, "schema.sql")) as f:
    cur.executescript(f.read())

# ---- Load skills ----
skills_df = pd.read_csv(os.path.join(DATA, "skills_master.csv"))
skills_df.rename(columns={"skill": "skill_name"}, inplace=True)
skills_df.to_sql("skills", conn, if_exists="append", index=False)

skill_id_map = dict(pd.read_sql("SELECT skill_id, skill_name FROM skills", conn)
                     .set_index("skill_name")["skill_id"])

# ---- Load companies ----
companies_df = pd.read_csv(os.path.join(DATA, "companies.csv"))
companies_load = companies_df.rename(columns={"company": "company_name"})[
    ["company_name", "role", "min_cgpa", "max_backlogs", "branches_allowed", "package_lpa", "category"]
]
companies_load.to_sql("companies", conn, if_exists="append", index=False)

company_id_map = dict(pd.read_sql("SELECT company_id, company_name FROM companies", conn)
                       .set_index("company_name")["company_id"])

# company_required_skills
crs_rows = []
for _, row in companies_df.iterrows():
    cid = company_id_map[row["company"]]
    for sk in [s.strip() for s in row["required_skills"].split(",")]:
        if sk in skill_id_map:
            crs_rows.append((cid, skill_id_map[sk]))
cur.executemany("INSERT OR IGNORE INTO company_required_skills VALUES (?,?)", crs_rows)

# ---- Load students ----
students_df = pd.read_csv(os.path.join(DATA, "students.csv"))
students_load = students_df[["student_id", "name", "branch", "cgpa", "backlogs",
                              "projects", "internships", "certifications",
                              "communication_score", "placed"]]
students_load.to_sql("students", conn, if_exists="append", index=False)

# student_skills
ss_rows = []
for _, row in students_df.iterrows():
    for sk in row["skills"].split(";"):
        sk = sk.strip()
        if sk in skill_id_map:
            ss_rows.append((row["student_id"], skill_id_map[sk]))
cur.executemany("INSERT OR IGNORE INTO student_skills VALUES (?,?)", ss_rows)

conn.commit()
conn.close()
print(f"Database built at {DB_PATH}")
