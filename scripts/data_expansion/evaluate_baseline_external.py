"""Evaluate the deployed baseline on project DEV and the new external splits.

Reports binary metrics, the best threshold satisfying FPR <= 0.01, the frozen
three-class operating point (0.25/0.75), and auth-path-specific error rates.
"""
import json
import os
import re
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
os.makedirs(OUT, exist_ok=True)

AUTH_RE = re.compile(
    r"(?:^|/)(login|signin|sign-in|sign_in|auth|account|accounts|verify|verification|"
    r"password|oauth|register|signup|sign-up|security|checkout|payment|billing|"
    r"wp-login\.php|login\.php|signin\.php)(?:/|$|[.?])",
    re.I,
)

def auth_path(url):
    try:
        p = str(url).split("://", 1)[1]
        path = p.split("/", 1)[1] if "/" in p else ""
        return int(bool(AUTH_RE.search("/" + path.split("?")[0])))
    except Exception:
        return 0

def load_split(path, cols=("url", "label")):
    df = pd.read_csv(path, usecols=list(cols))
    if "is_auth_path" not in df.columns:
        df["is_auth_path"] = df["url"].map(auth_path)
    return df

def evaluate(name, y, s):
    met = compute_metrics(y, s, threshold=0.5)
    met["ece"] = expected_calibration_error(y, s)
    fpr, tpr, thr = roc_curve(y, s)
    ok = fpr <= 0.01
    best_recall = float(tpr[ok].max()) if ok.any() else 0.0
    best_thr = float(thr[ok][int(np.argmax(tpr[ok]))]) if ok.any() else 1.0
    met_at_1pct = compute_metrics(y, s, threshold=best_thr)
    # frozen three-class: <0.25 legit, 0.25-0.75 review, >=0.75 phishing
    pred3 = np.where(s >= 0.75, 1, np.where(s < 0.25, 0, 2))
    legit = y == 0
    phish = y == 1
    met3 = {
        "phishing_recall": float((pred3[phish] == 1).mean()) if phish.any() else None,
        "phishing_detected_incl_review": float((pred3[phish] >= 1).mean()) if phish.any() else None,
        "legit_fpr": float((pred3[legit] == 1).mean()) if legit.any() else None,
        "review_rate": float((pred3 == 2).mean()),
        "review_rate_legit": float((pred3[legit] == 2).mean()) if legit.any() else None,
        "review_rate_phish": float((pred3[phish] == 2).mean()) if phish.any() else None,
    }
    return {
        "n": int(len(y)),
        "positives": int(phish.sum()),
        "negatives": int(legit.sum()),
        "at_0.5": met,
        "best_threshold_fpr_le_0.01": {"threshold": best_thr, **met_at_1pct},
        "three_class_0.25_0.75": met3,
    }

art = joblib.load(os.path.join(ROOT, "models/versions/M1_LR_HARDNEG.joblib"))
model, vec = art["model"], art["vectorizer"]

datasets = {
    "DEV": os.path.join(ROOT, "data/splits/DEV.csv"),
    "EXTERNAL_DEV": os.path.join(ROOT, "data/integrated/external_dev.csv"),
    "EXTERNAL_TEST": os.path.join(ROOT, "data/integrated/external_test.csv"),
}

results = {}
for name, path in datasets.items():
    df = load_split(path)
    s = model.predict_proba(vec.transform(df["url"].astype(str).tolist()))[:, 1]
    y = df["label"].astype(int).values
    results[name] = evaluate(name, y, s)
    print(f"\n=== {name} ===")
    print(f"n={len(y)} pos={int((y==1).sum())} neg={int((y==0).sum())}")
    m = results[name]["at_0.5"]
    print(f"@0.5: acc={m['accuracy']:.4f} rec={m['recall']:.4f} fpr={m['fpr']:.4f} "
          f"prec={m['precision']:.4f} f1={m['f1']:.4f} auc={m['roc_auc']:.4f} pr_auc={m['pr_auc']:.4f}")
    b = results[name]["best_threshold_fpr_le_0.01"]
    print(f"@FPR<=0.01: thr={b['threshold']:.4f} rec={b['recall']:.4f} fpr={b['fpr']:.4f} prec={b['precision']:.4f}")
    t3 = results[name]["three_class_0.25_0.75"]
    print(f"3-class: rec={t3['phishing_recall']:.4f} fpr={t3['legit_fpr']:.4f} "
          f"review={t3['review_rate']:.4f} review_legit={t3['review_rate_legit']:.4f}")

    # auth-path-specific diagnostics
    if "is_auth_path" in df.columns:
        auth = df["is_auth_path"].astype(int).values == 1
        if auth.any():
            for lab, labname in [(0, "legit_auth"), (1, "phish_auth")]:
                mask = auth & (y == lab)
                if mask.any():
                    print(f"  {labname}: n={int(mask.sum())} mean_score={s[mask].mean():.4f} "
                          f"score>=0.5={(s[mask]>=0.5).mean():.4f} score>=0.75={(s[mask]>=0.75).mean():.4f}")

with open(os.path.join(OUT, "baseline_external_eval.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
print(f"\nSaved {OUT}/baseline_external_eval.json")
