"""
Generates a synthetic student dataset for the Placement Intelligence Platform.
Run: python3 generate_data.py
Produces: students.csv (in the same folder)
"""
import random
import csv
import pandas as pd

random.seed(42)

BRANCHES = ["CSE", "IT", "ECE", "EEE", "MECH", "CIVIL"]

skills_df = pd.read_csv("skills_master.csv")
ALL_SKILLS = skills_df["skill"].tolist()

FIRST_NAMES = ["Aarav","Vivaan","Aditya","Ishaan","Kabir","Ananya","Diya","Meera",
               "Priya","Rohan","Sanjay","Kavya","Nikhil","Pooja","Arjun","Sneha",
               "Rahul","Neha","Karthik","Divya"]
LAST_NAMES = ["Sharma","Verma","Iyer","Reddy","Nair","Gupta","Menon","Rao",
              "Patel","Singh","Kumar","Das","Pillai","Joshi","Chatterjee"]

N_STUDENTS = 400

def random_skills():
    n = random.randint(3, 14)
    return random.sample(ALL_SKILLS, n)

rows = []
for i in range(1, N_STUDENTS + 1):
    name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    branch = random.choice(BRANCHES)
    cgpa = round(random.uniform(5.5, 9.8), 2)
    backlogs = random.choices([0, 1, 2, 3], weights=[60, 20, 12, 8])[0]
    skills = random_skills()
    projects = random.randint(0, 6)
    internships = random.randint(0, 3)
    certifications = random.randint(0, 5)
    communication_score = random.randint(1, 10)  # self/mock-interview rated

    # ---- Rule-based "ground truth" placement label used to train the model ----
    # This mimics historical placement outcomes so the ML model has a signal to learn.
    score = 0
    score += (cgpa - 5.5) * 8            # cgpa impact
    score -= backlogs * 6                # backlog penalty
    score += min(len(skills), 12) * 2.2  # skill breadth
    score += projects * 2.5
    score += internships * 4
    score += certifications * 1.5
    score += communication_score * 1.8
    score += random.gauss(0, 8)          # noise

    placed = 1 if score > 45 else 0

    rows.append({
        "student_id": i,
        "name": name,
        "branch": branch,
        "cgpa": cgpa,
        "backlogs": backlogs,
        "skills": ";".join(skills),
        "projects": projects,
        "internships": internships,
        "certifications": certifications,
        "communication_score": communication_score,
        "placed": placed
    })

df = pd.DataFrame(rows)
df.to_csv("students.csv", index=False)
print(f"Generated {len(df)} synthetic student records -> students.csv")
print(df["placed"].value_counts(normalize=True))
