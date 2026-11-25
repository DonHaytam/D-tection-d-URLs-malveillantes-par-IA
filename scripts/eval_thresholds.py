"""Evaluate threshold configurations on DEV (M1_LR_HARDNEG model)."""
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
        if s < low:
            out.append("LEGITIMATE")
        elif s >= high:
            out.append("PHISHING")
        else:
            out.append("NEEDS_REVIEW")
    return np.array(out)

def evaluate_thresholds(scores, y, low, high):
    preds = three_class(scores, low, high)
    # Binary: PHISHING = positive
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
    # Also: if NEEDS_REVIEW counts as "not phishing" for FNR (false negatives = phishing not caught)
    fn_total = int(((y==1) & (preds!="PHISHING")).sum())
    return {
        "low": low, "high": high,
        "recall": recall, "precision": precision, "f1": f1,
        "fpr": fpr, "specificity": spec,
        "tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn),
        "fn_total (phishing not PHISHING)": fn_total,
        "n_LEGITIMATE": n_leg, "n_NEEDS_REVIEW": n_rev, "n_PHISHING": n_phi,
        "review_rate": review_rate,
    }

# Evaluate proposed + current + alternatives
configs = [
    (0.05, 0.85),  # current
    (0.25, 0.75),  # proposed
    (0.10, 0.90),
    (0.15, 0.85),
    (0.20, 0.80),
    (0.30, 0.70),
    (0.10, 0.80),
    (0.20, 0.75),
]

results = []
for low, high in configs:
    r = evaluate_thresholds(scores, ydev, low, high)
    results.append(r)
    print(f"\nlow={low} high={high}:")
    print(f"  Recall={r['recall']:.4f} Precision={r['precision']:.4f} F1={r['f1']:.4f} FPR={r['fpr']:.4f} Spec={r['specificity']:.4f}")
    print(f"  LEGITIMATE={r['n_LEGITIMATE']} NEEDS_REVIEW={r['n_NEEDS_REVIEW']} PHISHING={r['n_PHISHING']} review_rate={r['review_rate']:.4f}")
    print(f"  TP={r['tp']} FP={r['fp']} TN={r['tn']} FN={r['fn']} (phishing not caught={r['fn_total (phishing not PHISHING)']})")

# Save
import pandas as pd
rdf = pd.DataFrame(results)
rdf.to_csv(os.path.join(ROOT, "reports/tables/threshold_evaluation_proposed.csv"), index=False)
with open(os.path.join(ROOT, "reports/tables/threshold_evaluation_proposed.json"), "w") as f:
    json.dump(results, f, indent=2)
print("\nSaved threshold_evaluation_proposed.csv/.json")
print("\n=== SUMMARY ===")
print(rdf[["low","high","recall","precision","f1","fpr","specificity","n_LEGITIMATE","n_NEEDS_REVIEW","n_PHISHING","review_rate"]].to_string(index=False))
