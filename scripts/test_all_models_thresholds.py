"""Test all models with all threshold combinations."""
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
from src.features.feature_pipeline import build_numeric_features
Xdev_num = build_numeric_features(Xdev)

# Load all models
model_files = {
    "M1_LR": ("text", "M1_LR.joblib"),
    "M2_SVM": ("text", "M2_SVM.joblib"),
    "M3_RF": ("num", "M3_RF.joblib"),
    "M4_GB": ("num", "M4_GB.joblib"),
    "M5_XGBOOST": ("num", "M5_XGBOOST.joblib"),
    "M6_HYBRID": ("hybrid", "M6_HYBRID.joblib"),
    "M1_HARDNEG": ("text", "M1_LR_HARDNEG.joblib"),
}

models = {}
for name, (kind, fn) in model_files.items():
    art = joblib.load(os.path.join(ROOT, "models/versions", fn))
    models[name] = (kind, art)

# Threshold combinations to test
thresholds = [(0.05, 0.85), (0.10, 0.80), (0.15, 0.75), (0.20, 0.70),
              (0.25, 0.65), (0.25, 0.75), (0.30, 0.70), (0.30, 0.65),
              (0.35, 0.60), (0.40, 0.55), (0.10, 0.70), (0.20, 0.65)]

def three_class(scores, low, high):
    out = []
    for s in scores:
        if s < low: out.append("LEGITIMATE")
        elif s >= high: out.append("PHISHING")
        else: out.append("NEEDS_REVIEW")
    return np.array(out)

def get_scores(name, kind, art):
    model = art["model"]
    if kind == "text":
        vec = art["vectorizer"]
        return model.predict_proba(vec.transform(Xdev))[:, 1]
    elif kind == "num":
        fnames = art["feature_names"]
        X = Xdev_num[fnames]
        return model.predict_proba(X)[:, 1]
    else:
        return model.predict_proba(Xdev)[:, 1]

# Evaluate all models x all thresholds
all_results = []
for mname, (kind, art) in models.items():
    sc = get_scores(mname, kind, art)
    for low, high in thresholds:
        preds = three_class(sc, low, high)
        binary_pred = (preds == "PHISHING").astype(int)
        tn, fp, fn, tp = confusion_matrix(ydev, binary_pred, labels=[0,1]).ravel()
        recall = tp/(tp+fn) if (tp+fn) else 0
        precision = tp/(tp+fp) if (tp+fp) else 0
        f1 = 2*precision*recall/(precision+recall) if (precision+recall) else 0
        fpr = fp/(fp+tn) if (fp+tn) else 0
        n_leg = int((preds=="LEGITIMATE").sum())
        n_rev = int((preds=="NEEDS_REVIEW").sum())
        n_phi = int((preds=="PHISHING").sum())
        all_results.append({
            "model": mname, "low": low, "high": high,
            "recall": recall, "precision": precision, "f1": f1,
            "fpr": fpr, "tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn),
            "n_LEGITIMATE": n_leg, "n_NEEDS_REVIEW": n_rev, "n_PHISHING": n_phi,
            "review_rate": n_rev/len(preds)
        })

rdf = pd.DataFrame(all_results)
# Best per model (by F1)
print("=== BEST THRESHOLD PER MODEL (by F1) ===")
best_per_model = rdf.loc[rdf.groupby("model")["f1"].idxmax()]
print(best_per_model[["model","low","high","recall","precision","f1","fpr","n_LEGITIMATE","n_NEEDS_REVIEW","n_PHISHING","review_rate"]].to_string(index=False))

# Best overall (F1)
best_overall = rdf.loc[rdf["f1"].idxmax()]
print(f"\n=== BEST OVERALL (by F1) ===")
print(f"Model: {best_overall['model']}, low={best_overall['low']}, high={best_overall['high']}")
print(f"  Recall={best_overall['recall']:.4f} Precision={best_overall['precision']:.4f} F1={best_overall['f1']:.4f} FPR={best_overall['fpr']:.4f}")
print(f"  LEGITIMATE={best_overall['n_LEGITIMATE']} NEEDS_REVIEW={best_overall['n_NEEDS_REVIEW']} PHISHING={best_overall['n_PHISHING']}")

# Feasible (FPR <= 0.01) best by recall
feasible = rdf[rdf["fpr"] <= 0.01]
if len(feasible) > 0:
    best_feasible = feasible.loc[feasible["recall"].idxmax()]
    print(f"\n=== BEST FEASIBLE (FPR<=0.01, by recall) ===")
    print(f"Model: {best_feasible['model']}, low={best_feasible['low']}, high={best_feasible['high']}")
    print(f"  Recall={best_feasible['recall']:.4f} FPR={best_feasible['fpr']:.4f} F1={best_feasible['f1']:.4f}")

# Save
rdf.to_csv(os.path.join(ROOT, "reports/tables/all_models_all_thresholds.csv"), index=False)
with open(os.path.join(ROOT, "reports/tables/all_models_all_thresholds.json"), "w") as f:
    json.dump(all_results, f, indent=2)
print("\nSaved all_models_all_thresholds.csv/.json")
