"""Evaluate soft-voting blends of the deployed model and external-data candidates."""
import json
import os
import sys

sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import roc_curve

from src.evaluation.metrics import compute_metrics, expected_calibration_error

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
OUT = os.path.join(ROOT, "reports", "data_expansion_public")
CAND = os.path.join(ROOT, "models", "versions", "candidates")

def evaluate(y, s):
    y = np.asarray(y).astype(int); s = np.asarray(s).astype(float)
    met = compute_metrics(y, s, threshold=0.5)
    met["ece"] = expected_calibration_error(y, s)
    fpr, tpr, thr = roc_curve(y, s)
    ok = fpr <= 0.01
    best_thr = float(thr[ok][int(np.argmax(tpr[ok]))]) if ok.any() else 1.0
    met_1 = compute_metrics(y, s, threshold=best_thr)
    pred3 = np.where(s >= 0.75, 1, np.where(s < 0.25, 0, 2))
    legit = y == 0; phish = y == 1
    return {
        "at_0.5": met,
        "best_threshold_fpr_le_0.01": {"threshold": best_thr, **met_1},
        "three_class_0.25_0.75": {
            "phishing_recall": float((pred3[phish] == 1).mean()),
            "legit_fpr": float((pred3[legit] == 1).mean()),
            "review_rate": float((pred3 == 2).mean()),
        },
    }

def load_scores(path, urls):
    art = joblib.load(path)
    return art["model"].predict_proba(art["vectorizer"].transform(urls))[:, 1]

DEV = pd.read_csv(os.path.join(ROOT, "data/splits/DEV.csv"))
EXT_TEST = pd.read_csv(os.path.join(ROOT, "data/integrated/external_test.csv"))
dev_urls = DEV["url"].astype(str).tolist()
ext_urls = EXT_TEST["url"].astype(str).tolist()
y_dev = DEV["label"].astype(int).values
y_ext = EXT_TEST["label"].astype(int).values

base_path = os.path.join(ROOT, "models/versions/M1_LR_HARDNEG.joblib")
base_dev = load_scores(base_path, dev_urls)
base_ext = load_scores(base_path, ext_urls)
print("baseline loaded")

candidates = {
    "EXT_RANDOM_40K": os.path.join(CAND, "EXT_RANDOM_40K.joblib"),
    "EXT_RANDOM_80K": os.path.join(CAND, "EXT_RANDOM_80K.joblib"),
    "EXT_HARD_20K": os.path.join(CAND, "EXT_HARD_20K.joblib"),
    "EXT_HARD_40K": os.path.join(CAND, "EXT_HARD_40K.joblib"),
}

results = {"baseline": {"dev": evaluate(y_dev, base_dev), "external_test": evaluate(y_ext, base_ext)}}
for name, path in candidates.items():
    c_dev = load_scores(path, dev_urls)
    c_ext = load_scores(path, ext_urls)
    results[name] = {"dev": evaluate(y_dev, c_dev), "external_test": evaluate(y_ext, c_ext)}
    for w in [0.25, 0.5, 0.75]:
        b_dev = (1 - w) * base_dev + w * c_dev
        b_ext = (1 - w) * base_ext + w * c_ext
        key = f"blend_{name}_w{w}"
        results[key] = {"dev": evaluate(y_dev, b_dev), "external_test": evaluate(y_ext, b_ext)}

with open(os.path.join(OUT, "ensemble_eval.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(f"{'model':32s} {'dev_rec@1%':>10s} {'dev_fpr@1%':>10s} {'dev_auc':>8s} {'ext_rec@1%':>10s} {'ext_fpr@1%':>10s} {'ext_auc':>8s}")
for name, r in results.items():
    d = r["dev"]; e = r["external_test"]
    print(f"{name:32s} {d['best_threshold_fpr_le_0.01']['recall']:10.4f} "
          f"{d['best_threshold_fpr_le_0.01']['fpr']:10.4f} {d['at_0.5']['roc_auc']:8.4f} "
          f"{e['best_threshold_fpr_le_0.01']['recall']:10.4f} "
          f"{e['best_threshold_fpr_le_0.01']['fpr']:10.4f} {e['at_0.5']['roc_auc']:8.4f}")
