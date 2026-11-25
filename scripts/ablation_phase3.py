"""Phase 3 — Feature ablation study."""
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
Xtr = TRAIN["url"].astype(str).tolist()
ytr = TRAIN["label"].astype(int).values
Xdev = DEV["url"].astype(str).tolist()
ydev = DEV["label"].astype(int).values

def next_exp_id():
    existing = sorted(os.listdir(os.path.join(ROOT, "experiments/results")))
    return f"EXP{len(existing)+1:03d}"

# Ablation configurations
ablations = {
    "char_tfidf_only": lambda urls: TfidfVectorizer(analyzer="char", ngram_range=(3,5), min_df=3, max_features=20000, lowercase=True, sublinear_tf=True).fit_transform(urls),
}

# We'll do: char TF-IDF only, char TF-IDF without suspicious tokens (not feasible easily),
# so we do: full char TF-IDF, and char TF-IDF on URL without scheme
results = []

# 1. Full char TF-IDF (baseline)
print("Ablation 1: Full char TF-IDF")
vec = TfidfVectorizer(analyzer="char", ngram_range=(3,5), min_df=3, max_features=20000, lowercase=True, sublinear_tf=True)
Xtr_c = vec.fit_transform(Xtr)
Xdev_c = vec.transform(Xdev)
t0 = time.time()
m = LogisticRegression(C=1.0, class_weight="balanced", solver="saga", max_iter=2000, random_state=42, n_jobs=-1)
m.fit(Xtr_c, ytr)
tr = time.time() - t0
sc = m.predict_proba(Xdev_c)[:, 1]
met = compute_metrics(ydev, sc); met["ece"] = expected_calibration_error(ydev, sc)
print(f"  acc={met['accuracy']:.4f} rec={met['recall']:.4f} fpr={met['fpr']:.4f} auc={met['roc_auc']:.4f}")
results.append({"config": "char_tfidf_full", "metrics": met, "train_time": tr})

# 2. Char TF-IDF on URL without scheme
print("\nAblation 2: Char TF-IDF (URL without scheme)")
def strip_scheme(urls):
    return [u.split("://",1)[-1] if "://" in u else u for u in urls]
Xtr2 = strip_scheme(Xtr); Xdev2 = strip_scheme(Xdev)
vec2 = TfidfVectorizer(analyzer="char", ngram_range=(3,5), min_df=3, max_features=20000, lowercase=True, sublinear_tf=True)
Xtr_c2 = vec2.fit_transform(Xtr2)
Xdev_c2 = vec2.transform(Xdev2)
t0 = time.time()
m2 = LogisticRegression(C=1.0, class_weight="balanced", solver="saga", max_iter=2000, random_state=42, n_jobs=-1)
m2.fit(Xtr_c2, ytr)
tr2 = time.time() - t0
sc2 = m2.predict_proba(Xdev_c2)[:, 1]
met2 = compute_metrics(ydev, sc2); met2["ece"] = expected_calibration_error(ydev, sc2)
print(f"  acc={met2['accuracy']:.4f} rec={met2['recall']:.4f} fpr={met2['fpr']:.4f} auc={met2['roc_auc']:.4f}")
results.append({"config": "char_tfidf_no_scheme", "metrics": met2, "train_time": tr2})

# 3. Char TF-IDF on host only
print("\nAblation 3: Char TF-IDF (host only)")
def host_only(urls):
    return [ (u.split("://")[-1].split("/")[0] if "://" in u else u.split("/")[0]) for u in urls]
Xtr3 = host_only(Xtr); Xdev3 = host_only(Xdev)
vec3 = TfidfVectorizer(analyzer="char", ngram_range=(3,5), min_df=3, max_features=20000, lowercase=True, sublinear_tf=True)
Xtr_c3 = vec3.fit_transform(Xtr3)
Xdev_c3 = vec3.transform(Xdev3)
t0 = time.time()
m3 = LogisticRegression(C=1.0, class_weight="balanced", solver="saga", max_iter=2000, random_state=42, n_jobs=-1)
m3.fit(Xtr_c3, ytr)
tr3 = time.time() - t0
sc3 = m3.predict_proba(Xdev_c3)[:, 1]
met3 = compute_metrics(ydev, sc3); met3["ece"] = expected_calibration_error(ydev, sc3)
print(f"  acc={met3['accuracy']:.4f} rec={met3['recall']:.4f} fpr={met3['fpr']:.4f} auc={met3['roc_auc']:.4f}")
results.append({"config": "char_tfidf_host_only", "metrics": met3, "train_time": tr3})

# Save
import json as _j
with open(os.path.join(ROOT, "reports/tables/feature_ablation.json"), "w") as f:
    _j.dump(results, f, indent=2, default=str)
print("\nSaved feature_ablation.json")

# Print summary
print("\n=== ABLATION SUMMARY ===")
for r in results:
    m = r["metrics"]
    print(f"{r['config']:25s} acc={m['accuracy']:.4f} rec={m['recall']:.4f} fpr={m['fpr']:.4f} auc={m['roc_auc']:.4f} ece={m['ece']:.4f}")
