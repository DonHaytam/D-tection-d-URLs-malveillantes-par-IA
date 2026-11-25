"""Choose three-class thresholds for the hybrid model on DEV."""
import json
import os
import sys

sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

import numpy as np
import pandas as pd
import joblib

from src.features.hybrid_reputation_features import load_tranco_rank, transform_with_artifact
from src.evaluation.metrics import compute_metrics

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
OUT = os.path.join(ROOT, "reports", "data_expansion_public")
DEV = pd.read_csv(os.path.join(ROOT, "data/splits/DEV.csv"))
y = DEV["label"].astype(int).values
urls = DEV["url"].astype(str).tolist()

art = joblib.load(os.path.join(ROOT, "models/versions/M1_HYBRID_REP_V2.joblib"))
tranco = load_tranco_rank(ROOT)
X = transform_with_artifact(art, urls, tranco)
s = art["model"].predict_proba(X)[:, 1]
np.save(os.path.join(OUT, "hybrid_dev_scores.npy"), s)
print("scored", len(s))

def metrics(low, high):
    pred = np.where(s >= high, 1, np.where(s < low, 0, 2))
    legit = y == 0; phish = y == 1
    return {
        "low": low, "high": high,
        "strict_recall": float((pred[phish] == 1).mean()),
        "detected_incl_review": float((pred[phish] >= 1).mean()),
        "fpr": float((pred[legit] == 1).mean()),
        "review_rate": float((pred == 2).mean()),
        "review_rate_legit": float((pred[legit] == 2).mean()),
        "review_rate_phish": float((pred[phish] == 2).mean()),
        "missed_phish": float((pred[phish] == 0).mean()),
    }

rows = []
for high in [0.70, 0.75, 0.80, 0.85, 0.88, 0.90, 0.903, 0.92, 0.95]:
    rows.append(metrics(0.25, high))
for low in [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]:
    rows.append(metrics(low, 0.903))

print(f"{'low':>5s} {'high':>6s} {'strict':>7s} {'detected':>9s} {'fpr':>7s} {'review':>7s} {'missed':>7s}")
for r in rows:
    print(f"{r['low']:5.2f} {r['high']:6.3f} {r['strict_recall']:7.4f} {r['detected_incl_review']:9.4f} "
          f"{r['fpr']:7.4f} {r['review_rate']:7.4f} {r['missed_phish']:7.4f}")

with open(os.path.join(OUT, "hybrid_thresholds.json"), "w", encoding="utf-8") as f:
    json.dump(rows, f, indent=2)
