"""Final model selection: update to M2_SVM with best thresholds."""
import sys, os, json
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import confusion_matrix

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
DEV = pd.read_csv(os.path.join(ROOT, "data/splits/DEV.csv"))
ydev = DEV["label"].astype(int).values
Xdev = DEV["url"].astype(str).tolist()

# Best model: M2_SVM with thresholds (0.4, 0.55)
art = joblib.load(os.path.join(ROOT, "models/versions/M2_SVM.joblib"))
model = art["model"]; vec = art["vectorizer"]
scores = model.predict_proba(vec.transform(Xdev))[:, 1]

low, high = 0.4, 0.55
preds = np.array(["LEGITIMATE" if s < low else ("PHISHING" if s >= high else "NEEDS_REVIEW") for s in scores])
binary_pred = (preds == "PHISHING").astype(int)
tn, fp, fn, tp = confusion_matrix(ydev, binary_pred, labels=[0,1]).ravel()
recall = tp/(tp+fn); precision = tp/(tp+fp); f1 = 2*precision*recall/(precision+recall)
fpr = fp/(fp+tn); spec = tn/(tn+fp)
print(f"M2_SVM with thresholds ({low}, {high}):")
print(f"  Recall={recall:.4f} Precision={precision:.4f} F1={f1:.4f} FPR={fpr:.4f} Spec={spec:.4f}")
print(f"  LEGITIMATE={(preds=='LEGITIMATE').sum()} NEEDS_REVIEW={(preds=='NEEDS_REVIEW').sum()} PHISHING={(preds=='PHISHING').sum()}")
print(f"  TP={tp} FP={fp} TN={tn} FN={fn}")

# Update metadata.json
import json as _j
metadata = {
    "model_version": "M2_SVM",
    "model_name": "Linear SVM (char TF-IDF) - best F1",
    "representation": "char_tfidf_3_5",
    "low_threshold": low,
    "high_threshold": high,
    "dev_metrics": {
        "accuracy": float((tp+tn)/len(ydev)),
        "precision": float(precision),
        "recall": float(recall),
        "fpr": float(fpr),
        "f1": float(f1),
        "roc_auc": 0.9583,
        "pr_auc": 0.9669,
        "brier": 0.0818,
        "ece": 0.0560
    },
    "production_gate": "BLOCKED",
    "note": "Best model by F1-score. Does NOT meet production gate (FPR 0.0446 > 0.01)."
}
with open(os.path.join(ROOT, "models/versions/metadata.json"), "w") as f:
    _j.dump(metadata, f, indent=2)
print("Updated metadata.json")

# Update decision_policy.py
dp_path = os.path.join(ROOT, "src/policy/decision_policy.py")
with open(dp_path, "r") as f:
    dp = f.read()
dp = dp.replace("LOW_DEFAULT = 0.25", "LOW_DEFAULT = 0.4")
dp = dp.replace("HIGH_DEFAULT = 0.75", "HIGH_DEFAULT = 0.55")
with open(dp_path, "w") as f:
    f.write(dp)
print("Updated decision_policy.py")

# Update predictor.py
pred_path = os.path.join(ROOT, "src/inference/predictor.py")
with open(pred_path, "r") as f:
    pred = f.read()
pred = pred.replace("self.low = self.metadata.get(\"low_threshold\", 0.25)",
                    "self.low = self.metadata.get(\"low_threshold\", 0.4)")
pred = pred.replace("self.high = self.metadata.get(\"high_threshold\", 0.75)",
                    "self.high = self.metadata.get(\"high_threshold\", 0.55)")
with open(pred_path, "w") as f:
    f.write(pred)
print("Updated predictor.py")

# Update frontend HTML
html_path = os.path.join(ROOT, "deployment/frontend/index.html")
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()
html = html.replace("low=0.25 (legitime), high=0.75 (phishing)", "low=0.40 (legitime), high=0.55 (phishing)")
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)
print("Updated index.html")

# Update frontend app.py
app_path = os.path.join(ROOT, "deployment/frontend/app.py")
with open(app_path, "r", encoding="utf-8") as f:
    app = f.read()
app = app.replace("low=0.25 (legitime), high=0.75 (phishing)", "low=0.40 (legitime), high=0.55 (phishing)")
with open(app_path, "w", encoding="utf-8") as f:
    f.write(app)
print("Updated app.py")

# Update MODEL_CARD.md
mc_path = os.path.join(ROOT, "MODEL_CARD.md")
with open(mc_path, "r", encoding="utf-8") as f:
    mc = f.read()
mc = mc.replace("- `low` = 0.25 → LEGITIMATE", "- `low` = 0.40 → LEGITIMATE")
mc = mc.replace("- `high` = 0.75 → PHISHING", "- `high` = 0.55 → PHISHING")
mc = mc.replace("M1_LR (Logistic Regression, char TF-IDF)", "M2_SVM (Linear SVM, char TF-IDF)")
mc = mc.replace("M1_LR_HARDNEG", "M2_SVM")
mc = mc.replace("Recall : 0.8422 | **FPR** : 0.0381 | **ROC-AUC** : 0.9610",
                "Recall : 0.8383 | **FPR** : 0.0446 | **ROC-AUC** : 0.9583")
with open(mc_path, "w", encoding="utf-8") as f:
    f.write(mc)
print("Updated MODEL_CARD.md")

print("\nDone. Model switched to M2_SVM with thresholds (0.4, 0.55).")
