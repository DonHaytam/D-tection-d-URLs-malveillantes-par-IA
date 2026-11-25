"""Test many threshold combinations for all models."""
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

art = joblib.load(os.path.join(ROOT, "models/versions/M1_LR_HARDNEG.joblib"))
model = art["model"]; vec = art["vectorizer"]
scores = model.predict_proba(vec.transform(Xdev))[:, 1]

def three_class(scores, low, high):
    out = []
    for s in scores:
        if s < low: out.append("LEGITIMATE")
        elif s >= high: out.append("PHISHING")
        else: out.append("NEEDS_REVIEW")
    return np.array(out)

def evaluate(scores, y, low, high):
    preds = three_class(scores, low, high)
    binary_pred = (preds == "PHISHING").astype(int)
    tn, fp, fn, tp = confusion_matrix(y, binary_pred, labels=[0,1]).ravel()
    recall = tp/(tp+fn) if (tp+fn) else 0
    precision = tp/(tp+fp) if (tp+fp) else 0
    f1 = 2*precision*recall/(precision+recall) if (precision+recall) else 0
    fpr = fp/(fp+tn) if (fp+tn) else 0
    spec = tn/(tn+fp) if (tn+fp) else 0
    n_leg = int((preds=="LEGITIMATE").sum())
    n_rev = int((preds=="NEEDS_REVIEW").sum())
    n_phi = int((preds=="PHISHING").sum())
    review_rate = n_rev / len(preds)
    return {"low":low, "high":high, "recall":recall, "precision":precision, "f1":f1,
            "fpr":fpr, "specificity":spec, "tp":int(tp), "fp":int(fp), "tn":int(tn), "fn":int(fn),
            "n_LEGITIMATE":n_leg, "n_NEEDS_REVIEW":n_rev, "n_PHISHING":n_phi, "review_rate":review_rate}

# Many threshold combinations
configs = []
for low in [0.01, 0.02, 0.03, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]:
    for high in [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]:
        if low < high:
            configs.append((low, high))

results = []
for low, high in configs:
    r = evaluate(scores, ydev, low, high)
    results.append(r)

rdf = pd.DataFrame(results)
# Sort by F1 descending
rdf = rdf.sort_values("f1", ascending=False)
print("=== TOP 15 BY F1 ===")
print(rdf.head(15)[["low","high","recall","precision","f1","fpr","specificity","n_LEGITIMATE","n_NEEDS_REVIEW","n_PHISHING","review_rate"]].to_string(index=False))

# Feasible (FPR <= 0.01)
feasible = rdf[rdf["fpr"] <= 0.01].sort_values("recall", ascending=False)
print("\n=== FEASIBLE (FPR <= 0.01), sorted by recall ===")
print(feasible[["low","high","recall","precision","f1","fpr","n_LEGITIMATE","n_NEEDS_REVIEW","n_PHISHING","review_rate"]].to_string(index=False))

# High recall (>= 0.80)
hr = rdf[rdf["recall"] >= 0.80].sort_values("fpr")
print("\n=== HIGH RECALL (>= 0.80), sorted by FPR ===")
print(hr[["low","high","recall","precision","f1","fpr","n_LEGITIMATE","n_NEEDS_REVIEW","n_PHISHING","review_rate"]].to_string(index=False))

# Save
rdf.to_csv(os.path.join(ROOT, "reports/tables/all_thresholds_extended.csv"), index=False)
with open(os.path.join(ROOT, "reports/tables/all_thresholds_extended.json"), "w") as f:
    json.dump(results, f, indent=2)
print("\nSaved all_thresholds_extended.csv/.json")
print(f"Total configurations tested: {len(results)}")
