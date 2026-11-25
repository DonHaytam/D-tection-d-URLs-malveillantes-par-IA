"""Phase 8 — train M6 only (resume)."""
import sys, os, json, time
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

import numpy as np
import pandas as pd
import joblib
from src.models.model_registry import REGISTRY
from src.evaluation.metrics import compute_metrics, expected_calibration_error

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
TRAIN = pd.read_csv(os.path.join(ROOT, "data/splits/TRAIN.csv"))
DEV = pd.read_csv(os.path.join(ROOT, "data/splits/DEV.csv"))
Xtr_url = TRAIN["url"].astype(str).tolist()
ytr = TRAIN["label"].astype(int).values
Xdev_url = DEV["url"].astype(str).tolist()
ydev = DEV["label"].astype(int).values

def next_exp_id():
    existing = sorted(os.listdir(os.path.join(ROOT, "experiments/results")))
    return f"EXP{len(existing)+1:03d}"

name = "M6_HYBRID"
print("Training", name)
t0 = time.time()
model = REGISTRY[name]()
model.fit(Xtr_url, ytr)
tr_time = time.time() - t0
sc_dev = model.predict_proba(Xdev_url)[:, 1]
m_dev = compute_metrics(ydev, sc_dev)
m_dev["ece"] = expected_calibration_error(ydev, sc_dev)
t1 = time.time()
_ = model.predict_proba(Xdev_url[:100])[:, 1]
lat = (time.time() - t1) / 100 * 1000
mpath = os.path.join(ROOT, "models/versions", f"{name}.joblib")
joblib.dump({"model": model}, mpath)
exp = {"experiment_id": next_exp_id(), "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
       "dataset_version": "v1", "train_split": "TRAIN", "dev_split": "DEV",
       "n_train": len(ytr), "n_dev": len(ydev), "model_name": name,
       "representation": "hybrid_char_tfidf_plus_numeric",
       "hyperparameters": {}, "random_seed": 42, "metrics_dev": m_dev,
       "training_time_s": round(tr_time, 3), "inference_latency_ms_per_url": round(lat, 4),
       "model_artifact_path": mpath}
with open(os.path.join(ROOT, "experiments/results", exp["experiment_id"] + ".json"), "w") as f:
    json.dump(exp, f, indent=2, default=str)
print("Saved", exp["experiment_id"])
print(f"{name}: acc={m_dev['accuracy']:.4f} rec={m_dev['recall']:.4f} fpr={m_dev['fpr']:.4f} f1={m_dev['f1']:.4f} auc={m_dev['roc_auc']:.4f} prauc={m_dev['pr_auc']:.4f} brier={m_dev['brier']:.4f} ece={m_dev['ece']:.4f} lat={lat:.3f}ms train={tr_time:.1f}s")
# append to summary csv
import pandas as pd
summary_df = pd.DataFrame([{"model": name, "accuracy": m_dev["accuracy"], "precision": m_dev["precision"],
    "recall": m_dev["recall"], "fpr": m_dev["fpr"], "f1": m_dev["f1"],
    "roc_auc": m_dev["roc_auc"], "pr_auc": m_dev["pr_auc"], "brier": m_dev["brier"],
    "ece": m_dev["ece"], "latency_ms": lat, "train_time_s": tr_time}])
existing_path = os.path.join(ROOT, "reports/tables/model_comparison_dev.csv")
old = pd.read_csv(existing_path)
summary_df = pd.concat([old, summary_df], ignore_index=True)
summary_df.to_csv(existing_path, index=False)
print("Summary updated.")
