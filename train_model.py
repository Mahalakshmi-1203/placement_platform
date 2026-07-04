"""
Trains a Placement Readiness model (Logistic Regression) on the synthetic
student dataset, evaluates it, and exports:
  - readiness_model.pkl (sklearn pipeline)
  - model_weights.json (human-readable coefficients, used to power the
    lightweight JS version of the scorer in the interactive demo)
Run: python3 train_model.py
"""
import json
import os
import joblib
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, roc_auc_score

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "..", "data", "students.csv")

df = pd.read_csv(DATA)
df["num_skills"] = df["skills"].apply(lambda x: len(x.split(";")))

FEATURES = ["cgpa", "backlogs", "num_skills", "projects",
            "internships", "certifications", "communication_score"]
X = df[FEATURES]
y = df["placed"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("clf", LogisticRegression(max_iter=1000))
])
pipe.fit(X_train, y_train)

y_pred = pipe.predict(X_test)
y_proba = pipe.predict_proba(X_test)[:, 1]

print(classification_report(y_test, y_pred))
print("ROC-AUC:", round(roc_auc_score(y_test, y_proba), 3))

joblib.dump(pipe, os.path.join(BASE, "readiness_model.pkl"))

# Export weights in the ORIGINAL feature scale (approx) so the same scoring
# logic can be replicated in plain JS for the interactive demo, without
# needing a live Python server.
scaler = pipe.named_steps["scaler"]
clf = pipe.named_steps["clf"]

weights = {
    "features": FEATURES,
    "mean": scaler.mean_.tolist(),
    "scale": scaler.scale_.tolist(),
    "coef": clf.coef_[0].tolist(),
    "intercept": float(clf.intercept_[0]),
    "note": "score = sigmoid(intercept + sum(coef_i * (x_i - mean_i)/scale_i)) * 100"
}
with open(os.path.join(BASE, "model_weights.json"), "w") as f:
    json.dump(weights, f, indent=2)

print("\nSaved model -> readiness_model.pkl")
print("Saved portable weights -> model_weights.json")

# quick score function demo
def readiness_score(cgpa, backlogs, num_skills, projects, internships, certifications, communication_score):
    row = pd.DataFrame([{
        "cgpa": cgpa, "backlogs": backlogs, "num_skills": num_skills,
        "projects": projects, "internships": internships,
        "certifications": certifications, "communication_score": communication_score
    }])
    return round(pipe.predict_proba(row[FEATURES])[0][1] * 100, 1)

print("\nExample readiness score:", readiness_score(8.2, 0, 9, 3, 1, 2, 7))
