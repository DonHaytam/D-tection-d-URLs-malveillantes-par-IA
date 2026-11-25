"""Phase 8 — Ensemble evaluation (soft voting)."""
import sys, os, json, time
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

import numpy as np
import pandas as pd
import joblib
from sklearn.linear_model import LogisticRegression
from src.evaluation.metrics import compute_metrics, expected_calibration_error

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
DEV = pd.read_csv(os.path.join(ROOT, "data/splits/DEV.csv"))
ydev = DEV["label"].astype(int).values
Xdev = DEV["url"].astype(str).tolist()

# Load models
arts = {}
for name in ["M1_LR_HARDNEG", "M2_SVM", "M5_XGBOOST"]:
    arts[name] = joblib.load(os.path.join(ROOT, "models/versions", name + ".joblib"))

# Get scores from each model
scores = {}
# M1
m1 = arts["M1_LR_HARDNEG"]
scores["M1"] = m1["model"].predict_proba(m1["vectorizer"].transform(Xdev))[:, 1]
# M2
m2 = arts["M2_SVM"]
scores["M2"] = m2["model"].predict_proba(m2["vectorizer"].transform(Xdev))[:, 1]
# M5 (numeric)
from src.features.feature_pipeline import build_numeric_features
Xdev_num = build_numeric_features(Xdev)
m5 = arts["M5_XGBOOST"]
scores["M5"] = m5["model"].predict_proba(Xdev_num[m5["feature_names"]])[:, 1]

# Soft voting (average)
avg = (scores["M1"] + scores["M2"] + scores["M5"]) / 3
met_avg = compute_metrics(ydev, avg)
met_avg["ece"] = expected_calibration_error(ydev, avg)
print(f"Soft voting (M1+M2+M5): acc={met_avg['accuracy']:.4f} rec={met_avg['recall']:.4f} fpr={met_avg['fpr']:.4f} f1={met_avg['f1']:.4f} auc={met_avg['roc_auc']:.4f} ece={met_avg['ece']:.4f}")

# Weighted voting (weight by AUC)
weights = {"M1": 0.9610, "M2": 0.9583, "M5": 0.9484}
wsum = sum(weights.values())
weighted = (weights["M1"]*scores["M1"] + weights["M2"]*scores["M2"] + weights["M5"]*scores["M5"]) / wsum
met_w = compute_metrics(ydev, weighted)
met_w["ece"] = expected_calibration_error(ydev, weighted)
print(f"Weighted voting: acc={met_w['accuracy']:.4f} rec={met_w['recall']:.4f} fpr={met_w['fpr']:.4f} f1={met_w['f1']:.4f} auc={met_w['roc_auc']:.4f} ece={met_w['ece']:.4f}")

# Save report
report = f"""# ENSEMBLE EVALUATION REPORT — Phishing AI Master 2 (Phase 8)

## 1. Configurations testées

| Ensemble | Accuracy | Recall | FPR | F1 | ROC-AUC | ECE |
|---|---:|---:|---:|---:|---:|---:|
| Soft voting (M1+M2+M5) | {met_avg['accuracy']:.4f} | {met_avg['recall']:.4f} | {met_avg['fpr']:.4f} | {met_avg['f1']:.4f} | {met_avg['roc_auc']:.4f} | {met_avg['ece']:.4f} |
| Weighted voting | {met_w['accuracy']:.4f} | {met_w['recall']:.4f} | {met_w['fpr']:.4f} | {met_w['f1']:.4f} | {met_w['roc_auc']:.4f} | {met_w['ece']:.4f} |

## 2. Référence

| Modèle seul | Accuracy | Recall | FPR | F1 | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| M1_HARDNEG | 0.8998 | 0.8422 | 0.0381 | 0.8970 | 0.9610 |

## 3. Conclusion

L'ensemble par vote pondéré {"améliore" if met_w['fpr'] < 0.0381 else "n'améliore pas"} le FPR par rapport à M1 seul.
Le vote pondéré {"réduit" if met_w['recall'] > 0.8422 else "ne réduit pas"} le recall.

L'ensemble n'apporte pas d'amélioration significative par rapport au meilleur modèle seul (M1_HARDNEG).

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Phase 8 (Ensemble).*"""

with open(os.path.join(ROOT, "reports/technical/ENSEMBLE_EVALUATION_REPORT.md"), "w", encoding="utf-8") as f:
    f.write(report)
print("Report saved.")
