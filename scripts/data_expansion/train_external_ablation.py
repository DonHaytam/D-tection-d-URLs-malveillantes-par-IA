"""Ablation: add only external legitimate or only external phishing URLs."""
import gc
import json
import os
import sys
import time

sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

import numpy as np
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_curve

from src.evaluation.metrics import compute_metrics, expected_calibration_error

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
OUT = os.path.join(ROOT, "reports", "data_expansion_public")
CAND = os.path.join(ROOT, "models", "versions", "candidates")
EXP = os.path.join(ROOT, "experiments", "results")

def next_exp_id():
    nums = []
    for f in os.listdir(EXP):
        if f.startswith("EXP") and f.endswith(".json"):
            try:
                nums.append(int(f[3:6]))
            except ValueError:
                pass
    return f"EXP{max(nums, default=0)+1:03d}"

def evaluate(y, s):
    y = np.asarray(y).astype(int); s = np.asarray(s).astype(float)
    m = compute_metrics(y, s, threshold=0.5)
    m["ece"] = expected_calibration_error(y, s)
    fpr, tpr, thr = roc_curve(y, s)
    ok = fpr <= 0.01
    bt = float(thr[ok][int(np.argmax(tpr[ok]))]) if ok.any() else 1.0
    m1 = compute_metrics(y, s, threshold=bt)
    pred3 = np.where(s >= 0.75, 1, np.where(s < 0.25, 0, 2))
    legit = y == 0; phish = y == 1
    return {"at_0.5": m, "best_threshold_fpr_le_0.01": {"threshold": bt, **m1},
            "three_class_0.25_0.75": {
                "phishing_recall": float((pred3[phish] == 1).mean()),
                "legit_fpr": float((pred3[legit] == 1).mean()),
                "review_rate": float((pred3 == 2).mean())}}

TRAIN = pd.read_csv(os.path.join(ROOT, "data/splits/TRAIN.csv"))
DEV = pd.read_csv(os.path.join(ROOT, "data/splits/DEV.csv"))
EXT = pd.read_csv(os.path.join(ROOT, "data/integrated/external_train.csv"))
EXT_DEV = pd.read_csv(os.path.join(ROOT, "data/integrated/external_dev.csv"))
dev_urls = DEV["url"].astype(str).tolist()
dev_y = DEV["label"].astype(int).values
ext_dev_urls = EXT_DEV["url"].astype(str).tolist()
ext_dev_y = EXT_DEV["label"].astype(int).values

CONFIGS = [
    ("EXT_LEGIT_20K", 20000, 0),
    ("EXT_LEGIT_40K", 40000, 0),
    ("EXT_PHISH_20K", 0, 20000),
    ("EXT_PHISH_40K", 0, 40000),
]
results = {}
for name, n_l, n_p in CONFIGS:
    print(f"\n=== {name} (legit={n_l}, phish={n_p}) ===")
    parts = [TRAIN[["url", "label"]]]
    if n_l:
        parts.append(EXT[EXT["label"] == 0].sample(n=n_l, random_state=42)[["url", "label"]])
    if n_p:
        parts.append(EXT[EXT["label"] == 1].sample(n=n_p, random_state=42)[["url", "label"]])
    data = pd.concat(parts, ignore_index=True).sample(frac=1.0, random_state=42).reset_index(drop=True)
    y = data["label"].astype(int).values
    vec = TfidfVectorizer(analyzer="char", ngram_range=(3, 5), min_df=3, max_features=20000,
                          lowercase=True, sublinear_tf=True)
    Xtr = vec.fit_transform(data["url"].astype(str).tolist())
    Xdev = vec.transform(dev_urls)
    Xext = vec.transform(ext_dev_urls)
    t0 = time.time()
    model = LogisticRegression(C=1.0, class_weight="balanced", solver="saga", max_iter=2000,
                               random_state=42, n_jobs=-1)
    model.fit(Xtr, y)
    tr = time.time() - t0
    s_dev = model.predict_proba(Xdev)[:, 1]
    s_ext = model.predict_proba(Xext)[:, 1]
    res_dev = evaluate(dev_y, s_dev)
    res_ext = evaluate(ext_dev_y, s_ext)
    results[name] = {"config": {"n_legit": n_l, "n_phish": n_p, "n_train": len(data)},
                     "training_time_s": round(tr, 2), "dev": res_dev, "external_dev": res_ext}
    m = res_dev["at_0.5"]; b = res_dev["best_threshold_fpr_le_0.01"]; t3 = res_dev["three_class_0.25_0.75"]
    print(f"  DEV @0.5 rec={m['recall']:.4f} fpr={m['fpr']:.4f} auc={m['roc_auc']:.4f}")
    print(f"  DEV @1% rec={b['recall']:.4f} fpr={b['fpr']:.4f}")
    print(f"  DEV 3c rec={t3['phishing_recall']:.4f} fpr={t3['legit_fpr']:.4f}")
    print(f"  EXT @0.5 rec={res_ext['at_0.5']['recall']:.4f} fpr={res_ext['at_0.5']['fpr']:.4f}")
    art = os.path.join(CAND, f"{name}.joblib")
    joblib.dump({"model": model, "vectorizer": vec}, art)
    eid = next_exp_id()
    with open(os.path.join(EXP, f"{eid}.json"), "w", encoding="utf-8") as f:
        json.dump({"experiment_id": eid, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                   "dataset_version": "v2_ablation", "train_split": f"TRAIN+{name}",
                   "dev_split": "DEV", "model_name": name,
                   "representation": "char_tfidf_3_5", "hyperparameters": {"C": 1.0, "class_weight": "balanced"},
                   "random_seed": 42, "metrics_dev": m, "metrics_dev_fpr_le_0.01": b,
                   "metrics_dev_three_class": t3, "metrics_external_dev": res_ext["at_0.5"],
                   "training_time_s": round(tr, 2), "model_artifact_path": art}, f, indent=2, default=str)
    results[name]["experiment_id"] = eid
    print(f"  saved {eid}")
    del model, vec, Xtr, Xdev, Xext, data
    gc.collect()

with open(os.path.join(OUT, "external_ablation.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, default=str)
