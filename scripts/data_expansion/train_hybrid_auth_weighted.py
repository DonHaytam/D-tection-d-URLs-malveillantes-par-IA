"""Hybrid (char + numeric + Tranco) with auth-focused sample weights.

Combines the best representation from HYB_V2_FULL with the auth reweighting
idea, using only real URLs from TRAIN and EXTERNAL_TRAIN.
"""
import gc
import json
import os
import re
import sys
import time

sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master/scripts/data_expansion")

import numpy as np
import pandas as pd
import joblib
from scipy.sparse import hstack, csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_curve

from src.evaluation.metrics import compute_metrics, expected_calibration_error
from hybrid_features import load_tranco_rank, numeric_frame, is_auth_path

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
OUT = os.path.join(ROOT, "reports", "data_expansion_public")
CAND = os.path.join(ROOT, "models", "versions", "candidates")
EXP = os.path.join(ROOT, "experiments", "results")
BROAD_RE = re.compile(
    r"login|signin|sign-in|sign_in|logon|auth|account|verify|verification|password|"
    r"passwd|oauth|register|signup|sign-up|security|checkout|payment|billing|secure",
    re.I,
)


def next_exp_id():
    nums = []
    for f in os.listdir(EXP):
        if f.startswith("EXP") and f.endswith(".json"):
            try:
                nums.append(int(f[3:6]))
            except ValueError:
                pass
    return f"EXP{max(nums, default=0) + 1:03d}"


def evaluate(y, s):
    m = compute_metrics(y, s, threshold=0.5)
    m["ece"] = expected_calibration_error(y, s)
    fpr, tpr, thr = roc_curve(y, s)
    out = {"at_0.5": m}
    for target in [0.005, 0.01, 0.02, 0.0381, 0.05]:
        ok = fpr <= target
        if ok.any():
            t = float(thr[ok][int(np.argmax(tpr[ok]))])
            out[f"at_fpr_le_{target}"] = {"threshold": t, **compute_metrics(y, s, threshold=t)}
    pred3 = np.where(s >= 0.75, 1, np.where(s < 0.25, 0, 2))
    legit = y == 0
    phish = y == 1
    out["three_class_0.25_0.75"] = {
        "strict_recall": float((pred3[phish] == 1).mean()),
        "detected_incl_review": float((pred3[phish] >= 1).mean()),
        "fpr": float((pred3[legit] == 1).mean()),
        "review_rate": float((pred3 == 2).mean()),
    }
    return out


def auth_metrics(df, s, strict=True):
    y = df["label"].astype(int).values
    a = df["auth_strict"].astype(int).values == 1 if strict else df["auth_broad"].astype(int).values == 1
    out = {}
    for lab, name in [(0, "legit_auth"), (1, "phish_auth")]:
        m = a & (y == lab)
        if m.any():
            out[name] = {
                "n": int(m.sum()),
                "mean_score": float(s[m].mean()),
                "score_ge_0.5": float((s[m] >= 0.5).mean()),
                "score_ge_0.75": float((s[m] >= 0.75).mean()),
                "score_ge_0.903": float((s[m] >= 0.903).mean()),
            }
    return out


TRAIN = pd.read_csv(os.path.join(ROOT, "data/splits/TRAIN.csv"), usecols=["url", "label"])
DEV = pd.read_csv(os.path.join(ROOT, "data/splits/DEV.csv"), usecols=["url", "label"])
EXT_TRAIN = pd.read_csv(os.path.join(ROOT, "data/integrated/external_train.csv"), usecols=["url", "label"])
EXT_DEV = pd.read_csv(os.path.join(ROOT, "data/integrated/external_dev.csv"), usecols=["url", "label"])
for df in (TRAIN, DEV, EXT_TRAIN, EXT_DEV):
    df["auth_strict"] = df["url"].map(is_auth_path)
    df["auth_broad"] = df["url"].str.contains(BROAD_RE, regex=True).astype(int)

rng = np.random.default_rng(42)
ext_sample = pd.concat([
    EXT_TRAIN[EXT_TRAIN.label == 0].sample(n=20000, random_state=42),
    EXT_TRAIN[EXT_TRAIN.label == 1].sample(n=20000, random_state=42),
], ignore_index=True)
train = pd.concat([TRAIN, ext_sample], ignore_index=True).sample(frac=1.0, random_state=42).reset_index(drop=True)
train_urls = train["url"].astype(str).tolist()
y_train = train["label"].astype(int).values
auth_train = train["auth_strict"].astype(int).values
dev_urls = DEV["url"].astype(str).tolist()
y_dev = DEV["label"].astype(int).values
ext_urls = EXT_DEV["url"].astype(str).tolist()
y_ext = EXT_DEV["label"].astype(int).values
print(f"train={len(train)} legit_auth={((y_train==0)&(auth_train==1)).sum()} "
      f"phish_auth={((y_train==1)&(auth_train==1)).sum()}")

print("Loading Tranco...")
tranco = load_tranco_rank(ROOT)
print("Fitting char TF-IDF...")
t0 = time.time()
vec = TfidfVectorizer(analyzer="char", ngram_range=(3, 5), min_df=3, max_features=20000,
                      lowercase=True, sublinear_tf=True)
Xtr_char = vec.fit_transform(train_urls)
Xdev_char = vec.transform(dev_urls)
Xext_char = vec.transform(ext_urls)
print(f"  char {time.time()-t0:.1f}s shape={Xtr_char.shape}")
print("Building numeric frames...")
t0 = time.time()
Ntr = numeric_frame(train_urls, tranco)
Ndev = numeric_frame(dev_urls, tranco)
Next = numeric_frame(ext_urls, tranco)
print(f"  numeric {time.time()-t0:.1f}s shape={Ntr.shape}")
cols = list(Ntr.columns)
scaler = StandardScaler()
Ntr_s = scaler.fit_transform(Ntr[cols].values.astype(np.float32))
Ndev_s = scaler.transform(Ndev[cols].values.astype(np.float32))
Next_s = scaler.transform(Next[cols].values.astype(np.float32))
Xtr = hstack([Xtr_char, csr_matrix(Ntr_s)]).tocsr()
Xdev = hstack([Xdev_char, csr_matrix(Ndev_s)]).tocsr()
Xext = hstack([Xext_char, csr_matrix(Next_s)]).tocsr()

CONFIGS = [
    ("AUTH_HYB_W5", 5.0, 1.0),
    ("AUTH_HYB_W10", 10.0, 1.0),
    ("AUTH_HYB_W20", 20.0, 1.0),
]
results = {}
for name, w_legit_auth, w_phish_auth in CONFIGS:
    print(f"\n=== {name} (legit_auth_w={w_legit_auth}, phish_auth_w={w_phish_auth}) ===")
    sw = np.ones(len(train), dtype=np.float32)
    sw[(y_train == 0) & (auth_train == 1)] = w_legit_auth
    sw[(y_train == 1) & (auth_train == 1)] = w_phish_auth
    t0 = time.time()
    model = LogisticRegression(C=1.0, class_weight="balanced", solver="lbfgs", max_iter=300,
                               tol=1e-3, random_state=42, n_jobs=-1)
    model.fit(Xtr, y_train, sample_weight=sw)
    tr_time = time.time() - t0
    s_dev = model.predict_proba(Xdev)[:, 1]
    s_ext = model.predict_proba(Xext)[:, 1]
    res_dev = evaluate(y_dev, s_dev)
    res_ext = evaluate(y_ext, s_ext)
    res_dev["auth_strict"] = auth_metrics(DEV, s_dev, strict=True)
    res_dev["auth_broad"] = auth_metrics(DEV, s_dev, strict=False)
    res_ext["auth_strict"] = auth_metrics(EXT_DEV, s_ext, strict=True)
    results[name] = {"config": {"legit_auth_weight": w_legit_auth, "phish_auth_weight": w_phish_auth,
                                "n_train": int(len(train)), "n_features": int(Xtr.shape[1])},
                     "training_time_s": round(tr_time, 2), "dev": res_dev, "external_dev": res_ext}
    a = res_dev["at_0.5"]; b = res_dev["at_fpr_le_0.01"]; t3 = res_dev["three_class_0.25_0.75"]
    print(f"  DEV @0.5 rec={a['recall']:.4f} fpr={a['fpr']:.4f} auc={a['roc_auc']:.4f}")
    print(f"  DEV @1% rec={b['recall']:.4f} fpr={b['fpr']:.4f} thr={b['threshold']:.4f}")
    print(f"  DEV 3c rec={t3['strict_recall']:.4f} fpr={t3['fpr']:.4f}")
    print(f"  DEV legit_auth strict: {res_dev['auth_strict'].get('legit_auth')}")
    print(f"  DEV legit_auth broad: {res_dev['auth_broad'].get('legit_auth')}")
    ae = res_ext["at_0.5"]; be = res_ext["at_fpr_le_0.01"]
    print(f"  EXT @0.5 rec={ae['recall']:.4f} fpr={ae['fpr']:.4f} auc={ae['roc_auc']:.4f}")
    print(f"  EXT @1% rec={be['recall']:.4f} fpr={be['fpr']:.4f}")

    art_path = os.path.join(CAND, f"{name}.joblib")
    joblib.dump({"model": model, "vectorizer": vec, "scaler": scaler,
                 "numeric_feature_names": cols, "kind": "hybrid_char_numeric"}, art_path)
    eid = next_exp_id()
    with open(os.path.join(EXP, f"{eid}.json"), "w", encoding="utf-8") as f:
        json.dump({"experiment_id": eid, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                   "dataset_version": "v2_auth_hybrid", "train_split": "TRAIN+EXT40K",
                   "dev_split": "DEV", "model_name": name,
                   "representation": "char_tfidf_3_5 + numeric/structural + Tranco reputation",
                   "hyperparameters": {"C": 1.0, "class_weight": "balanced",
                                       "legit_auth_weight": w_legit_auth,
                                       "phish_auth_weight": w_phish_auth},
                   "random_seed": 42, "metrics_dev": a, "metrics_dev_fpr_le_0.01": b,
                   "metrics_dev_three_class": t3, "metrics_external_dev": ae,
                   "training_time_s": round(tr_time, 2), "model_artifact_path": art_path},
                  f, indent=2, default=str)
    results[name]["experiment_id"] = eid
    results[name]["artifact"] = art_path
    print(f"  saved {eid}")
    del model
    gc.collect()

with open(os.path.join(OUT, "auth_hybrid.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, default=str)

print("\n=== AUTH-HYBRID COMPARISON (DEV) ===")
print(f"{'model':22s} {'rec@.5':>8s} {'fpr@.5':>8s} {'auc':>7s} {'rec@1%':>8s} {'fpr@1%':>8s} {'3c_rec':>8s} {'3c_fpr':>8s}")
for name, r in results.items():
    a = r["dev"]["at_0.5"]; b = r["dev"]["at_fpr_le_0.01"]; t = r["dev"]["three_class_0.25_0.75"]
    print(f"{name:22s} {a['recall']:8.4f} {a['fpr']:8.4f} {a['roc_auc']:7.4f} "
          f"{b['recall']:8.4f} {b['fpr']:8.4f} {t['strict_recall']:8.4f} {t['fpr']:8.4f}")
