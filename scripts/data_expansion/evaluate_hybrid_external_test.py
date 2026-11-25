"""Held-out evaluation: baseline vs hybrid on EXTERNAL_TEST.

EXTERNAL_TEST domains are disjoint from TRAIN/DEV/LOCKED_TEST/INDEPENDENT and
from EXTERNAL_TRAIN/EXTERNAL_DEV. It is used once here as a final check.
"""
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
from src.features.hybrid_reputation_features import load_tranco_rank, transform_with_artifact

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
OUT = os.path.join(ROOT, "reports", "data_expansion_public")
os.makedirs(OUT, exist_ok=True)

TEST = pd.read_csv(os.path.join(ROOT, "data/integrated/external_test.csv"),
                   usecols=["url", "label", "source", "is_auth_path"])
y = TEST["label"].astype(int).values
urls = TEST["url"].astype(str).tolist()
print(f"EXTERNAL_TEST rows={len(TEST)} legit={(y==0).sum()} phish={(y==1).sum()}")


def chunked_scores(path, kind, chunk=20000):
    art = joblib.load(path)
    scores = []
    tranco = load_tranco_rank(ROOT) if kind == "hybrid" else None
    for i in range(0, len(urls), chunk):
        part = urls[i:i + chunk]
        if kind == "hybrid":
            X = transform_with_artifact(art, part, tranco)
        else:
            X = art["vectorizer"].transform(part)
        scores.append(art["model"].predict_proba(X)[:, 1])
        print(f"  {kind} scored {min(i+chunk, len(urls))}/{len(urls)}", flush=True)
    return np.concatenate(scores)


def evaluate(y_true, s):
    m = compute_metrics(y_true, s, threshold=0.5)
    m["ece"] = expected_calibration_error(y_true, s)
    fpr, tpr, thr = roc_curve(y_true, s)
    out = {"at_0.5": m}
    for target in [0.005, 0.01, 0.02, 0.0381, 0.05]:
        ok = fpr <= target
        if ok.any():
            t = float(thr[ok][int(np.argmax(tpr[ok]))])
            out[f"at_fpr_le_{target}"] = {"threshold": t, **compute_metrics(y_true, s, threshold=t)}
    # vectorized best F1
    order = np.argsort(-s)
    ys = y_true[order]
    tp = np.cumsum(ys == 1)
    fp = np.cumsum(ys == 0)
    fn = (y_true == 1).sum() - tp
    prec = tp / np.maximum(tp + fp, 1)
    rec = tp / np.maximum(tp + fn, 1)
    f1 = 2 * prec * rec / np.maximum(prec + rec, 1e-12)
    k = int(np.argmax(f1))
    out["best_f1"] = {"threshold": float(s[order][k]), "f1": float(f1[k]),
                      "precision": float(prec[k]), "recall": float(rec[k]),
                      "fpr": float(fp[k] / max((y_true == 0).sum(), 1))}
    return out


def three_class(y_true, s, low, high):
    pred = np.where(s >= high, 1, np.where(s < low, 0, 2))
    legit = y_true == 0
    phish = y_true == 1
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


def subset(y_true, s, mask, name):
    if not mask.any():
        return None
    m = compute_metrics(y_true[mask], s[mask], threshold=0.5)
    pred = np.where(s[mask] >= 0.75, 1, np.where(s[mask] < 0.25, 0, 2))
    yy = y_true[mask]
    return {
        "name": name, "n": int(mask.sum()),
        "positives": int((yy == 1).sum()), "negatives": int((yy == 0).sum()),
        "at_0.5": m,
        "three_class_0.25_0.75": {
            "strict_recall": float((pred[yy == 1] == 1).mean()) if (yy == 1).any() else None,
            "fpr": float((pred[yy == 0] == 1).mean()) if (yy == 0).any() else None,
            "review_rate": float((pred == 2).mean()),
        },
    }


base = chunked_scores(os.path.join(ROOT, "models/versions/M1_LR_HARDNEG.joblib"), "base")
hyb = chunked_scores(os.path.join(ROOT, "models/versions/M1_HYBRID_REP_V2.joblib"), "hybrid")

results = {}
for name, s in [("baseline", base), ("hybrid", hyb)]:
    r = evaluate(y, s)
    r["three_class_0.25_0.75"] = three_class(y, s, 0.25, 0.75)
    r["three_class_0.25_0.90"] = three_class(y, s, 0.25, 0.90)
    r["three_class_0.25_0.903"] = three_class(y, s, 0.25, 0.903)
    r["subsets"] = {}
    if "is_auth_path" in TEST.columns:
        auth = TEST["is_auth_path"].astype(int).values == 1
        r["subsets"]["legit_auth"] = subset(y, s, auth & (y == 0), "legit_auth")
        r["subsets"]["phish_auth"] = subset(y, s, auth & (y == 1), "phish_auth")
    for src in TEST["source"].astype(str).unique():
        sm = TEST["source"].astype(str).values == src
        r["subsets"][f"source:{src}"] = subset(y, s, sm, f"source:{src}")
    results[name] = r

with open(os.path.join(OUT, "external_test_hybrid.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, default=str)

print("\n=== EXTERNAL_TEST ===")
print(f"{'model':10s} {'rec@.5':>8s} {'fpr@.5':>8s} {'auc':>7s} {'rec@1%':>8s} {'fpr@1%':>8s} {'3c_rec':>8s} {'3c_fpr':>8s}")
for name, r in results.items():
    a = r["at_0.5"]; b = r["at_fpr_le_0.01"]; t = r["three_class_0.25_0.75"]
    print(f"{name:10s} {a['recall']:8.4f} {a['fpr']:8.4f} {a['roc_auc']:7.4f} "
          f"{b['recall']:8.4f} {b['fpr']:8.4f} {t['strict_recall']:8.4f} {t['fpr']:8.4f}")

for name, r in results.items():
    print(f"\n{name} three-class @0.25/0.903: {r['three_class_0.25_0.903']}")
    for k, v in r["subsets"].items():
        if v:
            print(f"  {k:28s} n={v['n']:6d} rec@.5={v['at_0.5']['recall']:.4f} "
                  f"fpr@.5={v['at_0.5']['fpr']:.4f} 3c_rec={v['three_class_0.25_0.75']['strict_recall']} "
                  f"3c_fpr={v['three_class_0.25_0.75']['fpr']}")
