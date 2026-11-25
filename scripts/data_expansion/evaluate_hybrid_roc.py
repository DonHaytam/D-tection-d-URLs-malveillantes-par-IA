"""Compare baseline vs hybrid ROC operating points and calibration transfer."""
import json
import os
import sys

sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master/scripts/data_expansion")

import numpy as np
import pandas as pd
import joblib
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_curve

from src.evaluation.metrics import compute_metrics, expected_calibration_error
from hybrid_features import load_tranco_rank, transform_with_artifact, is_auth_path

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
OUT = os.path.join(ROOT, "reports", "data_expansion_public")
CAND = os.path.join(ROOT, "models", "versions", "candidates")

DEV = pd.read_csv(os.path.join(ROOT, "data/splits/DEV.csv"))
EXT_DEV = pd.read_csv(os.path.join(ROOT, "data/integrated/external_dev.csv"))
y_dev = DEV["label"].astype(int).values
y_ext = EXT_DEV["label"].astype(int).values
dev_urls = DEV["url"].astype(str).tolist()
ext_urls = EXT_DEV["url"].astype(str).tolist()

tranco = load_tranco_rank(ROOT)

def evaluate(y, s, prefix=""):
    met = compute_metrics(y, s, threshold=0.5)
    met["ece"] = expected_calibration_error(y, s)
    fpr, tpr, thr = roc_curve(y, s)
    out = {"at_0.5": met}
    for target in [0.005, 0.01, 0.02, 0.0381, 0.05]:
        ok = fpr <= target
        if ok.any():
            t = float(thr[ok][int(np.argmax(tpr[ok]))])
            m = compute_metrics(y, s, threshold=t)
            out[f"at_fpr_le_{target}"] = {"threshold": t, **m}
    # best F1 threshold, vectorized
    order = np.argsort(-s)
    y_sorted = y[order]
    tp = np.cumsum(y_sorted == 1)
    fp = np.cumsum(y_sorted == 0)
    fn = (y == 1).sum() - tp
    precision = tp / np.maximum(tp + fp, 1)
    recall = tp / np.maximum(tp + fn, 1)
    f1 = 2 * precision * recall / np.maximum(precision + recall, 1e-12)
    k = int(np.argmax(f1))
    out["best_f1"] = {"threshold": float(s[order][k]), "f1": float(f1[k]),
                      "precision": float(precision[k]), "recall": float(recall[k]),
                      "fpr": float(fp[k] / max((y == 0).sum(), 1))}
    return out

def three_class(y, s, low=0.25, high=0.75):
    pred = np.where(s >= high, 1, np.where(s < low, 0, 2))
    legit = y == 0; phish = y == 1
    return {
        "low": low, "high": high,
        "phishing_recall": float((pred[phish] == 1).mean()),
        "legit_fpr": float((pred[legit] == 1).mean()),
        "review_rate": float((pred == 2).mean()),
    }

def optimize_three_class(y, s, max_fpr=0.01):
    """Find high threshold with FPR<=max_fpr, then low threshold maximizing review coverage."""
    fpr, tpr, thr = roc_curve(y, s)
    ok = fpr <= max_fpr
    high = float(thr[ok][int(np.argmax(tpr[ok]))]) if ok.any() else 1.0
    # low threshold: maximize phishing detected incl. review subject to review rate <= 0.25
    best = None
    for low in np.linspace(0.01, high - 0.01, 50):
        pred = np.where(s >= high, 1, np.where(s < low, 0, 2))
        legit = y == 0; phish = y == 1
        rec = (pred[phish] >= 1).mean()
        review = (pred == 2).mean()
        fpr_legit = (pred[legit] == 1).mean()
        if review <= 0.30:
            if best is None or rec > best["detected_incl_review"]:
                best = {"low": float(low), "high": high,
                        "detected_incl_review": float(rec),
                        "strict_recall": float((pred[phish] == 1).mean()),
                        "fpr": float(fpr_legit), "review_rate": float(review)}
    return best

results = {}

# Baseline
base = joblib.load(os.path.join(ROOT, "models/versions/M1_LR_HARDNEG.joblib"))
s_base = base["model"].predict_proba(base["vectorizer"].transform(dev_urls))[:, 1]
results["baseline"] = evaluate(y_dev, s_base)
results["baseline"]["three_class_0.25_0.75"] = three_class(y_dev, s_base)
results["baseline"]["three_class_optimized"] = optimize_three_class(y_dev, s_base)
print("baseline DEV @0.5:", {k: round(v, 4) for k, v in results["baseline"]["at_0.5"].items() if isinstance(v, float)})

for name in ["HYBRID_TRAIN", "HYBRID_EXT40K"]:
    path = os.path.join(CAND, f"{name}.joblib")
    if not os.path.exists(path):
        print("missing", path)
        continue
    art = joblib.load(path)
    X_dev = transform_with_artifact(art, dev_urls, tranco)
    s_hyb = art["model"].predict_proba(X_dev)[:, 1]
    results[name] = evaluate(y_dev, s_hyb)
    results[name]["three_class_0.25_0.75"] = three_class(y_dev, s_hyb)
    results[name]["three_class_optimized"] = optimize_three_class(y_dev, s_hyb)
    print(f"\n{name} DEV @0.5:", {k: round(v, 4) for k, v in results[name]["at_0.5"].items() if isinstance(v, float)})
    print(f"{name} best_f1:", {k: round(v, 4) for k, v in results[name]["best_f1"].items() if isinstance(v, float)})

    # calibration transfer: fit isotonic on EXTERNAL_DEV, apply to DEV
    X_ext = transform_with_artifact(art, ext_urls, tranco)
    s_ext = art["model"].predict_proba(X_ext)[:, 1]
    iso = IsotonicRegression(out_of_bounds="clip")
    iso.fit(s_ext, y_ext)
    s_cal = iso.predict(s_hyb)
    results[name]["isotonic_from_external_dev"] = evaluate(y_dev, s_cal)
    results[name]["isotonic_from_external_dev"]["three_class_0.25_0.75"] = three_class(y_dev, s_cal)
    results[name]["isotonic_from_external_dev"]["three_class_optimized"] = optimize_three_class(y_dev, s_cal)
    print(f"{name} calibrated(external dev) @0.5:",
          {k: round(v, 4) for k, v in results[name]["isotonic_from_external_dev"]["at_0.5"].items() if isinstance(v, float)})

    # Platt scaling on external dev
    platt = LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000)
    platt.fit(s_ext.reshape(-1, 1), y_ext)
    s_platt = platt.predict_proba(s_hyb.reshape(-1, 1))[:, 1]
    results[name]["platt_from_external_dev"] = evaluate(y_dev, s_platt)
    results[name]["platt_from_external_dev"]["three_class_0.25_0.75"] = three_class(y_dev, s_platt)
    print(f"{name} platt(external dev) @0.5:",
          {k: round(v, 4) for k, v in results[name]["platt_from_external_dev"]["at_0.5"].items() if isinstance(v, float)})

with open(os.path.join(OUT, "hybrid_roc_calibration.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, default=str)

print("\n=== RECALL AT FPR TARGETS (DEV) ===")
print(f"{'model':32s} " + " ".join(f"{t:>10}" for t in ["0.5%", "1%", "2%", "3.81%", "5%"]))
for name, r in results.items():
    vals = []
    for t in [0.005, 0.01, 0.02, 0.0381, 0.05]:
        k = f"at_fpr_le_{t}"
        vals.append(f"{r[k]['recall']:.4f}" if k in r else "n/a")
    print(f"{name:32s} " + " ".join(f"{v:>10}" for v in vals))
