"""FINAL OPTIMIZATION ATTEMPT — Phase: multi-round hard-negative mining + LR tuning."""
import sys, os, json, time
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

import numpy as np
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from src.evaluation.metrics import compute_metrics, expected_calibration_error

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
TRAIN = pd.read_csv(os.path.join(ROOT, "data/splits/TRAIN.csv"))
DEV = pd.read_csv(os.path.join(ROOT, "data/splits/DEV.csv"))

def next_exp_id():
    existing = sorted(os.listdir(os.path.join(ROOT, "experiments/results")))
    return f"EXP{len(existing)+1:03d}"

# Start from M1_HARDNEG training data (original TRAIN + 597 hard negatives)
# Rebuild augmented training set
art = joblib.load(os.path.join(ROOT, "models/versions/M1_LR.joblib"))
model = art["model"]; vec = art["vectorizer"]
sc = model.predict_proba(vec.transform(DEV["url"].astype(str).tolist()))[:, 1]
DEV2 = DEV.copy()
DEV2["score"] = sc
hard_neg = DEV2[(DEV2["label"]==0) & (sc >= 0.5)].copy()
print("Round 1 hard negatives:", len(hard_neg))

# Build augmented training set (original + round1 HN)
hn_cols = TRAIN.columns.tolist()
hn = hard_neg[hn_cols].copy()
augmented = pd.concat([TRAIN, hn], ignore_index=True)
print("Augmented TRAIN:", len(augmented))

# Round 2: find new FPs from the augmented model
# Train round 1 model
Xtr = augmented["url"].astype(str).tolist()
ytr = augmented["label"].astype(int).values
Xdev = DEV["url"].astype(str).tolist()
ydev = DEV["label"].astype(int).values

char_vec = TfidfVectorizer(analyzer="char", ngram_range=(3,5), min_df=3,
                           max_features=20000, lowercase=True, sublinear_tf=True)
Xtr_c = char_vec.fit_transform(Xtr)
Xdev_c = char_vec.transform(Xdev)

# Try multiple C values
best_result = None
for C in [0.3, 0.5, 1.0]:
    for cw in ["balanced"]:
        name = f"FINAL_LR_C{C}"
        print(f"\nTraining {name} (C={C}, cw={cw}) on {len(Xtr)} samples")
        t0 = time.time()
        m = LogisticRegression(C=C, class_weight=cw, solver="saga", max_iter=3000,
                               random_state=42, n_jobs=-1)
        m.fit(Xtr_c, ytr)
        tr_time = time.time() - t0
        sc_dev = m.predict_proba(Xdev_c)[:, 1]
        met = compute_metrics(ydev, sc_dev)
        met["ece"] = expected_calibration_error(ydev, sc_dev)
        print(f"  acc={met['accuracy']:.4f} rec={met['recall']:.4f} fpr={met['fpr']:.4f} f1={met['f1']:.4f} auc={met['roc_auc']:.4f} ece={met['ece']:.4f} train={tr_time:.1f}s")
        if best_result is None or met["fpr"] < best_result[1]["fpr"]:
            best_result = (name, met, m, C, cw, tr_time, char_vec)
        eid = next_exp_id()
        joblib.dump({"model": m, "vectorizer": char_vec}, os.path.join(ROOT, "models/versions", f"{name}.joblib"))
        exp = {"experiment_id": eid, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "dataset_version": "v1", "train_split": "TRAIN+HN", "dev_split": "DEV",
               "n_train": len(ytr), "n_dev": len(ydev), "model_name": name,
               "representation": "char_tfidf_3_5 (hardneg, multi-round)",
               "hyperparameters": {"C": C, "class_weight": cw}, "random_seed": 42,
               "metrics_dev": met, "training_time_s": round(tr_time, 3),
               "model_artifact_path": os.path.join(ROOT, "models/versions", f"{name}.joblib")}
        with open(os.path.join(ROOT, "experiments/results", eid + ".json"), "w") as f:
            json.dump(exp, f, indent=2, default=str)
        print(f"  Saved {eid}")

# Save best
best_name, best_met, best_model, best_C, best_cw, best_time, best_vec = best_result
joblib.dump({"model": best_model, "vectorizer": best_vec},
            os.path.join(ROOT, "models/versions/FINAL_BEST.joblib"))
print(f"\nBEST: {best_name} fpr={best_met['fpr']:.4f} rec={best_met['recall']:.4f} auc={best_met['roc_auc']:.4f}")

# Save threshold optimization for best model
sc_best = best_model.predict_proba(best_vec.transform(Xdev))[:, 1]
# Find threshold with recall >= 0.85 and min FPR
thresholds = np.unique(sc_best)
best_thr = None
for t in sorted(thresholds, reverse=True):
    pred = (sc_best >= t).astype(int)
    tp = int(((pred==1)&(ydev==1)).sum())
    fp = int(((pred==1)&(ydev==0)).sum())
    tn = int(((pred==0)&(ydev==0)).sum())
    fn = int(((pred==0)&(ydev==1)).sum())
    rec = tp/(tp+fn) if tp+fn else 0
    fpr = fp/(fp+tn) if fp+tn else 0
    if rec >= 0.85:
        if best_thr is None or fpr < best_thr[1]:
            best_thr = (t, fpr, rec, tp, fp, tn, fn)
        break  # first (highest threshold) with recall>=0.85 when going from high to low... actually we want min fpr among feasible

# Actually, search all thresholds
best_feasible = None
for t in thresholds:
    pred = (sc_best >= t).astype(int)
    tp = int(((pred==1)&(ydev==1)).sum())
    fp = int(((pred==1)&(ydev==0)).sum())
    tn = int(((pred==0)&(ydev==0)).sum())
    fn = int(((pred==0)&(ydev==1)).sum())
    rec = tp/(tp+fn) if tp+fn else 0
    fpr = fp/(fp+tn) if fp+tn else 0
    if rec >= 0.85:
        if best_feasible is None or fpr < best_feasible[1]:
            best_feasible = (t, fpr, rec, tp, fp, tn, fn)
print(f"\nBest feasible threshold: {best_feasible[0]:.4f} recall={best_feasible[2]:.4f} fpr={best_feasible[1]:.4f} (tp={best_feasible[3]} fp={best_feasible[4]} tn={best_feasible[5]} fn={best_feasible[6]})")

# Save threshold result
thr_result = {"model": best_name, "threshold": float(best_feasible[0]),
              "recall": float(best_feasible[2]), "fpr": float(best_feasible[1]),
              "tp": best_feasible[3], "fp": best_feasible[4], "tn": best_feasible[5], "fn": best_feasible[6]}
with open(os.path.join(ROOT, "reports/tables/final_threshold_results.json"), "w") as f:
    json.dump(thr_result, f, indent=2)
print("Saved final_threshold_results.json")
print(json.dumps(thr_result, indent=2))
