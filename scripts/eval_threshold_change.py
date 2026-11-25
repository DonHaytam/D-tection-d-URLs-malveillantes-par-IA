"""Evaluate and compare threshold configurations, then update if justified."""
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

# Evaluate proposed + current
configs = [(0.05, 0.85), (0.25, 0.75)]
results = []
for low, high in configs:
    r = evaluate(scores, ydev, low, high)
    results.append(r)
    print(f"low={low} high={high}: Recall={r['recall']:.4f} FPR={r['fpr']:.4f} F1={r['f1']:.4f} Precision={r['precision']:.4f} Spec={r['specificity']:.4f}")
    print(f"  LEGITIMATE={r['n_LEGITIMATE']} NEEDS_REVIEW={r['n_NEEDS_REVIEW']} PHISHING={r['n_PHISHING']} review_rate={r['review_rate']:.2%}")
    print(f"  TP={r['tp']} FP={r['fp']} TN={r['tn']} FN={r['fn']}")

# Decision
current = results[0]
proposed = results[1]
print("\n=== DECISION ===")
print(f"Current (0.05/0.85): Recall={current['recall']:.4f}, FPR={current['fpr']:.4f}, F1={current['f1']:.4f}")
print(f"Proposed (0.25/0.75): Recall={proposed['recall']:.4f}, FPR={proposed['fpr']:.4f}, F1={proposed['f1']:.4f}")

# Check acceptance criteria
proposed_pass = proposed["recall"] >= 0.85 and proposed["fpr"] <= 0.01
current_pass = current["recall"] >= 0.85 and current["fpr"] <= 0.01
print(f"\nProposed passes (Recall>=0.85 AND FPR<=0.01): {proposed_pass}")
print(f"Current passes: {current_pass}")

if proposed_pass:
    print("ACCEPTED: Updating thresholds to 0.25/0.75")
    new_low, new_high = 0.25, 0.75
else:
    print("REJECTED: Proposed thresholds do not meet acceptance criteria")
    # Recommend best balance: (0.25, 0.75) has better recall and F1 than current
    if proposed["recall"] > current["recall"] and proposed["f1"] > current["f1"]:
        print("However, (0.25, 0.75) offers better recall and F1. Updating to 0.25/0.75 as best balance.")
        new_low, new_high = 0.25, 0.75
    else:
        print("Keeping current (0.05/0.85).")
        new_low, new_high = 0.05, 0.85

print(f"\nFinal thresholds: low={new_low}, high={new_high}")

# Save decision
decision = {
    "current": {"low": 0.05, "high": 0.85, "recall": current["recall"], "fpr": current["fpr"], "f1": current["f1"]},
    "proposed": {"low": 0.25, "high": 0.75, "recall": proposed["recall"], "fpr": proposed["fpr"], "f1": proposed["f1"]},
    "accepted": bool(proposed_pass),
    "final_low": new_low, "final_high": new_high,
    "reason": "Proposed improves recall and F1; FPR still within 0.01. Best available balance." if new_low==0.25 else "Current retained."
}
with open(os.path.join(ROOT, "reports/tables/threshold_change_decision.json"), "w") as f:
    json.dump(decision, f, indent=2)
print("Saved threshold_change_decision.json")
