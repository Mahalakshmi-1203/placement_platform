"""
Resume Parser (rule-based NLP)
------------------------------
Extracts structured signals from a raw resume (txt/pdf/docx or pasted text):
  - skills (matched against skills_master.csv, incl. common synonyms)
  - CGPA / percentage
  - number of projects mentioned
  - number of internships mentioned
  - number of certifications mentioned

This is intentionally dependency-light (regex + keyword matching) so it runs
anywhere without downloading NLP models. It can be swapped for a spaCy /
transformer NER pipeline later without changing the rest of the platform.
"""
import re
import os
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
SKILLS_CSV = os.path.join(BASE, "..", "data", "skills_master.csv")

SYNONYMS = {
    "ml": "Machine Learning",
    "dl": "Deep Learning",
    "reactjs": "React",
    "react.js": "React",
    "node": "Node.js",
    "nodejs": "Node.js",
    "postgres": "PostgreSQL",
    "oops": "OOP",
    "dsa": "Data Structures",
    "data structures and algorithms": "Data Structures",
    "os": "Operating Systems",
    "cn": "Computer Networks",
    "power bi": "Power BI",
    "aws cloud": "AWS",
}


def load_skill_list():
    df = pd.read_csv(SKILLS_CSV)
    return df["skill"].tolist()


def extract_text_from_file(filepath):
    """Extract raw text from .txt, .pdf, or .docx resume files."""
    ext = filepath.lower().split(".")[-1]
    if ext == "txt":
        with open(filepath, "r", errors="ignore") as f:
            return f.read()
    elif ext == "pdf":
        import pdfplumber
        text = []
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                text.append(page.extract_text() or "")
        return "\n".join(text)
    elif ext == "docx":
        import docx
        d = docx.Document(filepath)
        return "\n".join(p.text for p in d.paragraphs)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def extract_skills(text, skill_list=None):
    if skill_list is None:
        skill_list = load_skill_list()
    text_lower = " " + text.lower() + " "

    # normalize common synonyms first
    for syn, canonical in SYNONYMS.items():
        pattern = r"(?<![a-zA-Z])" + re.escape(syn) + r"(?![a-zA-Z])"
        text_lower = re.sub(pattern, canonical.lower(), text_lower)

    found = []
    for skill in skill_list:
        pattern = r"(?<![a-zA-Z])" + re.escape(skill.lower()) + r"(?![a-zA-Z])"
        if re.search(pattern, text_lower):
            found.append(skill)
    return sorted(set(found))


def extract_cgpa(text):
    # matches "CGPA: 8.4", "CGPA - 8.4/10", "8.4 CGPA", "GPA 8.4"
    match = re.search(r"(?:cgpa|gpa)[^0-9]{0,5}(\d(?:\.\d{1,2})?)", text, re.I)
    if match:
        return float(match.group(1))
    match = re.search(r"(\d(?:\.\d{1,2})?)\s*(?:cgpa|gpa)", text, re.I)
    if match:
        return float(match.group(1))
    return None


def count_keyword_mentions(text, keywords):
    text_lower = text.lower()
    total = 0
    for kw in keywords:
        total += len(re.findall(r"(?<![a-zA-Z])" + re.escape(kw) + r"(?![a-zA-Z])", text_lower))
    return total


def parse_resume(text):
    skills = extract_skills(text)
    cgpa = extract_cgpa(text)
    projects = count_keyword_mentions(text, ["project", "projects"])
    internships = count_keyword_mentions(text, ["intern", "internship", "internships"])
    certifications = count_keyword_mentions(text, ["certification", "certificate", "certified"])

    return {
        "skills": skills,
        "num_skills": len(skills),
        "cgpa": cgpa,
        "projects_mentioned": projects,
        "internships_mentioned": internships,
        "certifications_mentioned": certifications,
    }


if __name__ == "__main__":
    sample = """
    Aditya Sharma
    CGPA: 8.3/10, CSE Final Year

    Skills: Python, Java, Data Structures, SQL, Machine Learning, Git, React

    Projects:
    1. Built a placement prediction ML model using scikit-learn and pandas.
    2. Developed a full-stack web app using React and Node.js.

    Internship: Data Analyst Intern at XYZ Pvt Ltd (2 months)
    Certifications: AWS Cloud Practitioner, Google Data Analytics Certificate
    """
    result = parse_resume(sample)
    print(result)
