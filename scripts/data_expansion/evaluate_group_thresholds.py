"""Group-specific decision thresholds for platform vs ordinary URLs.

The full platform-masked model already ranks platform pages reasonably
(AUC ~0.90 on the DEV platform subset) but a single global threshold spends
too little of the FPR budget there.  This script searches two thresholds
(platform / other) under the same global 1% FPR constraint.
"""
import json
import os
import sys

sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master/scripts/data_expansion")

import numpy as np
import pandas as pd
import joblib
from scipy.sparse import hstack, csr_matrix

from src.evaluation.metrics import compute_metrics, expected_calibration_error
from hybrid_features import load_tranco_rank
from platform_shared import platform_frame, platform_of

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
OUT = os.path.join(ROOT, "reports", "data_expansion_public")
CAND = os.path.join(ROOT, "models", "versions", "candidates")


def score_full(art, urls, tranco):
    Xc = art["vectorizer"].transform(urls)
    N = platform_frame(urls, tranco, with_flags=False)
    Ns = art["scaler"].transform(N[art["numeric_feature_names"]].values.astype(np.float32))
    X = hstack([Xc, csr_matrix(Ns)]).tocsr()
    return art["model"].predict_proba(X)[:, 1]


def eval_pair(y, s, mask, t_other, t_plat):
    pred = np.where(mask, s >= t_plat, s >= t_other)
    rec = float(pred[y == 1].mean())
    fpr = float(pred[y == 0].mean())
    return rec, fpr, pred


art = joblib.load(os.path.join(CAND, "PLATFORM_MASK.joblib"))
tranco = load_tranco_rank(ROOT)
results = {}
for name, path in [("dev", "data/splits/DEV.csv"), ("ext_dev", "data/integrated/external_dev.csv")]:
    df = pd.read_csv(os.path.join(ROOT, path), usecols=["url", "label"])
    y = df["label"].astype(int).values
    mask = df["url"].map(lambda u: platform_of(u)[0] != "").values
    s = score_full(art, df["url"].astype(str).tolist(), tranco)
    best = None
    # Coarse grid then a local refinement.
    for t_other in np.arange(0.60, 0.995, 0.01):
        for t_plat in np.arange(0.05, 0.995, 0.01):
            rec, fpr, _ = eval_pair(y, s, mask, t_other, t_plat)
            if fpr <= 0.01 and (best is None or rec > best[0]):
                best = (rec, fpr, float(t_other), float(t_plat))
    if best:
        b_rec, b_fpr, b_to, b_tp = best
        for t_other in np.arange(max(0.3, b_to - 0.02), min(0.999, b_to + 0.02) + 1e-9, 0.002):
            for t_plat in np.arange(max(0.01, b_tp - 0.02), min(0.999, b_tp + 0.02) + 1e-9, 0.002):
                rec, fpr, _ = eval_pair(y, s, mask, t_other, t_plat)
                if fpr <= 0.01 and rec > best[0]:
                    best = (rec, fpr, float(t_other), float(t_plat))
    single = None
    for t in np.arange(0.3, 0.995, 0.005):
        rec = float((s[y == 1] >= t).mean())
        fpr = float((s[y == 0] >= t).mean())
        if fpr <= 0.01 and (single is None or rec > single[0]):
            single = (rec, fpr, float(t))
    results[name] = {"best_two_threshold": best, "best_single_threshold": single,
                     "n": int(len(df)), "n_platform": int(mask.sum())}
    print(name, "single", single, "two", best)
    if best:
        rec, fpr, to, tp = best
        pred = np.where(mask, s >= tp, s >= to)
        for grp, m in [("platform", mask), ("other", ~mask)]:
            print(f"  {grp}: n={int(m.sum())} recall={float(pred[m & (y==1)].mean()):.4f} "
                  f"fpr={float(pred[m & (y==0)].mean()):.4f}")

with open(os.path.join(OUT, "group_thresholds.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, default=str)
print("Saved", os.path.join(OUT, "group_thresholds.json"))
