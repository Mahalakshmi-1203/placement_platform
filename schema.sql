-- =========================================================
-- Student Placement Intelligence Platform - Database Schema
-- =========================================================

CREATE TABLE IF NOT EXISTS students (
    student_id       INTEGER PRIMARY KEY,
    name             TEXT NOT NULL,
    branch           TEXT NOT NULL,
    cgpa             REAL NOT NULL,
    backlogs         INTEGER NOT NULL DEFAULT 0,
    projects         INTEGER NOT NULL DEFAULT 0,
    internships      INTEGER NOT NULL DEFAULT 0,
    certifications   INTEGER NOT NULL DEFAULT 0,
    communication_score INTEGER,
    readiness_score  REAL,              -- filled in by the ML model
    placed           INTEGER            -- 1/0, historical/label (NULL for current students)
);

CREATE TABLE IF NOT EXISTS skills (
    skill_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_name  TEXT UNIQUE NOT NULL,
    category    TEXT
);

CREATE TABLE IF NOT EXISTS student_skills (
    student_id  INTEGER REFERENCES students(student_id),
    skill_id    INTEGER REFERENCES skills(skill_id),
    PRIMARY KEY (student_id, skill_id)
);

CREATE TABLE IF NOT EXISTS companies (
    company_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name     TEXT NOT NULL,
    role             TEXT,
    min_cgpa         REAL,
    max_backlogs     INTEGER,
    branches_allowed TEXT,
    package_lpa      REAL,
    category         TEXT
);

CREATE TABLE IF NOT EXISTS company_required_skills (
    company_id  INTEGER REFERENCES companies(company_id),
    skill_id    INTEGER REFERENCES skills(skill_id),
    PRIMARY KEY (company_id, skill_id)
);

-- Result of running the eligibility checker for a student against all companies
CREATE TABLE IF NOT EXISTS eligibility_results (
    student_id      INTEGER REFERENCES students(student_id),
    company_id      INTEGER REFERENCES companies(company_id),
    eligible        INTEGER,   -- 1/0
    skill_match_pct REAL,
    missing_skills  TEXT,
    PRIMARY KEY (student_id, company_id)
);

-- Useful views for reporting / Power BI --------------------------------

CREATE VIEW IF NOT EXISTS v_student_summary AS
SELECT
    s.student_id,
    s.name,
    s.branch,
    s.cgpa,
    s.backlogs,
    s.readiness_score,
    COUNT(DISTINCT ss.skill_id) AS total_skills
FROM students s
LEFT JOIN student_skills ss ON s.student_id = ss.student_id
GROUP BY s.student_id;

CREATE VIEW IF NOT EXISTS v_eligibility_report AS
SELECT
    er.student_id,
    s.name,
    s.branch,
    c.company_name,
    c.role,
    c.package_lpa,
    er.eligible,
    er.skill_match_pct,
    er.missing_skills
FROM eligibility_results er
JOIN students s ON s.student_id = er.student_id
JOIN companies c ON c.company_id = er.company_id;
