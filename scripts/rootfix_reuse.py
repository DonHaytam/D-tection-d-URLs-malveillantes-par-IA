"""Rootfix: reuse existing vectorizer, add hard negatives."""
import sys, os, json, time
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

import numpy as np
import pandas as pd
import joblib
from sklearn.linear_model import LogisticRegression
from src.evaluation.metrics import compute_metrics, expected_calibration_error

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
TRAIN = pd.read_csv(os.path.join(ROOT, "data/splits/TRAIN.csv"))
DEV = pd.read_csv(os.path.join(ROOT, "data/splits/DEV.csv"))

# Load existing vectorizer from M1
m1_art = joblib.load(os.path.join(ROOT, "models/versions/M1_LR.joblib"))
vec = m1_art["vectorizer"]

# Load hard negatives (sample)
hn = pd.read_csv(os.path.join(ROOT, "data/interim/hn_legit_auth.csv"))
hn_sample = hn.sample(n=5000, random_state=42).reset_index(drop=True)

# Build augmented training set
for c in TRAIN.columns:
    if c not in hn_sample.columns:
        hn_sample[c] = None
hn_aligned = hn_sample[TRAIN.columns]
augmented = pd.concat([TRAIN, hn_aligned], ignore_index=True)
print(f"Augmented TRAIN: {len(augmented)} (was {len(TRAIN)})")

Xtr = augmented["url"].astype(str).tolist()
ytr = augmented["label"].astype(int).values
Xdev = DEV["url"].astype(str).tolist()
ydev = DEV["label"].astype(int).values

# Transform (reuse existing vectorizer, no fit)
Xtr_c = vec.transform(Xtr)
Xdev_c = vec.transform(Xdev)
print(f"Feature shape: {Xtr_c.shape}")

t0 = time.time()
m = LogisticRegression(C=1.0, class_weight="balanced", solver="saga", max_iter=3000, random_state=42, n_jobs=-1)
m.fit(Xtr_c, ytr)
tr = time.time() - t0
sc = m.predict_proba(Xdev_c)[:, 1]
met = compute_metrics(ydev, sc)
met["ece"] = expected_calibration_error(ydev, sc)
print(f"  acc={met['accuracy']:.4f} rec={met['recall']:.4f} fpr={met['fpr']:.4f} f1={met['f1']:.4f} auc={met['roc_auc']:.4f} ece={met['ece']:.4f} train={tr:.1f}s")

# Diagnostic URLs
diag_urls = [
    "https://www.paypal.com/signin",
    "https://www.dropbox.com/login",
    "https://github.com/login",
    "https://accounts.google.com/signin",
    "https://login.microsoftonline.com/",
    "https://www.amazon.com/ap/signin",
    "https://www.apple.com/shop/account/home",
    "https://www.linkedin.com/login",
]
diag_scores = m.predict_proba(vec.transform(diag_urls))[:, 1]
print("\n=== DIAGNOSTIC URLS ===")
for u, s in zip(diag_urls, diag_scores):
    print(f"  {s*100:6.2f}%  {u}")

# Save
import json as _j
eid = f"EXP{len(os.listdir(os.path.join(ROOT, 'experiments/results')))+1:03d}"
joblib.dump({"model": m, "vectorizer": vec}, os.path.join(ROOT, "models/versions", "ROOTFIX_HN_REUSE.joblib"))
exp = {"experiment_id": eid, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
       "dataset_version": "v1", "train_split": "TRAIN+HN5K", "dev_split": "DEV",
       "n_train": len(ytr), "n_dev": len(ydev), "model_name": "ROOTFIX_HN_REUSE",
       "representation": "char_tfidf_3_5 (reuse existing vec) + 5k hard-neg",
       "hyperparameters": {"C": 1.0, "class_weight": "balanced"}, "random_seed": 42,
       "metrics_dev": met, "training_time_s": round(tr, 3),
       "model_artifact_path": os.path.join(ROOT, "models/versions", "ROOTFIX_HN_REUSE.joblib")}
with open(os.path.join(ROOT, "experiments/results", eid + ".json"), "w") as f:
    _j.dump(exp, f, indent=2, default=str)
print(f"\nSaved {eid}")
