"""Phase 8 (resume) — Train M3-M6 (M1, M2 already done)."""
import sys, os, json, time
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

import numpy as np
import pandas as pd
import joblib

from src.data.validation import normalize_url
from src.features.feature_pipeline import build_numeric_features
from src.models.model_registry import REGISTRY
from src.evaluation.metrics import compute_metrics, expected_calibration_error

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
TRAIN = pd.read_csv(os.path.join(ROOT, "data/splits/TRAIN.csv"))
DEV = pd.read_csv(os.path.join(ROOT, "data/splits/DEV.csv"))
Xtr_url = TRAIN["url"].astype(str).tolist()
ytr = TRAIN["label"].astype(int).values
Xdev_url = DEV["url"].astype(str).tolist()
ydev = DEV["label"].astype(int).values

os.makedirs(os.path.join(ROOT, "models/versions"), exist_ok=True)
os.makedirs(os.path.join(ROOT, "experiments/results"), exist_ok=True)

def next_exp_id():
    existing = sorted(os.listdir(os.path.join(ROOT, "experiments/results")))
    return f"EXP{len(existing)+1:03d}"

def save_exp(exp):
    path = os.path.join(ROOT, "experiments/results", exp["experiment_id"] + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(exp, f, indent=2, default=str)
    print("Saved", path)

# Numeric features
print("Building numeric features...")
Xtr_num = build_numeric_features(Xtr_url)
Xdev_num = build_numeric_features(Xdev_url)
print("numeric shape", Xtr_num.shape)
feature_names = list(Xtr_num.columns)
joblib.dump(feature_names, os.path.join(ROOT, "models/versions", "feature_names.joblib"))

results_summary = []

# M3 Random Forest
name = "M3_RF"
print("Training", name)
t0 = time.time()
model = REGISTRY[name](n_estimators=200, max_depth=None, min_samples_leaf=2)
model.fit(Xtr_num, ytr)
tr_time = time.time() - t0
sc_dev = model.predict_proba(Xdev_num)[:, 1]
m_dev = compute_metrics(ydev, sc_dev)
m_dev["ece"] = expected_calibration_error(ydev, sc_dev)
t1 = time.time()
_ = model.predict_proba(Xdev_num.iloc[:100])[:, 1]
lat = (time.time() - t1) / 100 * 1000
mpath = os.path.join(ROOT, "models/versions", f"{name}.joblib")
joblib.dump({"model": model, "feature_names": feature_names}, mpath)
exp = {"experiment_id": next_exp_id(), "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
       "dataset_version": "v1", "train_split": "TRAIN", "dev_split": "DEV",
       "n_train": len(ytr), "n_dev": len(ydev), "model_name": name,
       "representation": "numeric_lexical_structural",
       "hyperparameters": {"n_estimators": 200, "min_samples_leaf": 2},
       "random_seed": 42, "metrics_dev": m_dev,
       "training_time_s": round(tr_time, 3), "inference_latency_ms_per_url": round(lat, 4),
       "model_artifact_path": mpath}
save_exp(exp)
results_summary.append((name, m_dev, lat, tr_time))

# M4 Gradient Boosting
name = "M4_GB"
print("Training", name)
t0 = time.time()
model = REGISTRY[name](n_estimators=200, learning_rate=0.1, max_depth=3)
model.fit(Xtr_num, ytr)
tr_time = time.time() - t0
sc_dev = model.predict_proba(Xdev_num)[:, 1]
m_dev = compute_metrics(ydev, sc_dev)
m_dev["ece"] = expected_calibration_error(ydev, sc_dev)
t1 = time.time()
_ = model.predict_proba(Xdev_num.iloc[:100])[:, 1]
lat = (time.time() - t1) / 100 * 1000
mpath = os.path.join(ROOT, "models/versions", f"{name}.joblib")
joblib.dump({"model": model, "feature_names": feature_names}, mpath)
exp = {"experiment_id": next_exp_id(), "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
       "dataset_version": "v1", "train_split": "TRAIN", "dev_split": "DEV",
       "n_train": len(ytr), "n_dev": len(ydev), "model_name": name,
       "representation": "numeric_lexical_structural",
       "hyperparameters": {"n_estimators": 200, "learning_rate": 0.1, "max_depth": 3},
       "random_seed": 42, "metrics_dev": m_dev,
       "training_time_s": round(tr_time, 3), "inference_latency_ms_per_url": round(lat, 4),
       "model_artifact_path": mpath}
save_exp(exp)
results_summary.append((name, m_dev, lat, tr_time))

# M5 XGBoost
name = "M5_XGBOOST"
print("Training", name)
t0 = time.time()
model = REGISTRY[name](n_estimators=200, learning_rate=0.1, max_depth=6)
model.fit(Xtr_num, ytr)
tr_time = time.time() - t0
sc_dev = model.predict_proba(Xdev_num)[:, 1]
m_dev = compute_metrics(ydev, sc_dev)
m_dev["ece"] = expected_calibration_error(ydev, sc_dev)
t1 = time.time()
_ = model.predict_proba(Xdev_num.iloc[:100])[:, 1]
lat = (time.time() - t1) / 100 * 1000
mpath = os.path.join(ROOT, "models/versions", f"{name}.joblib")
joblib.dump({"model": model, "feature_names": feature_names}, mpath)
exp = {"experiment_id": next_exp_id(), "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
       "dataset_version": "v1", "train_split": "TRAIN", "dev_split": "DEV",
       "n_train": len(ytr), "n_dev": len(ydev), "model_name": name,
       "representation": "numeric_lexical_structural",
       "hyperparameters": {"n_estimators": 200, "learning_rate": 0.1, "max_depth": 6},
       "random_seed": 42, "metrics_dev": m_dev,
       "training_time_s": round(tr_time, 3), "inference_latency_ms_per_url": round(lat, 4),
       "model_artifact_path": mpath}
save_exp(exp)
results_summary.append((name, m_dev, lat, tr_time))

# M6 Hybrid
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
       "hyperparameters": {},
       "random_seed": 42, "metrics_dev": m_dev,
       "training_time_s": round(tr_time, 3), "inference_latency_ms_per_url": round(lat, 4),
       "model_artifact_path": mpath}
save_exp(exp)
results_summary.append((name, m_dev, lat, tr_time))

print("\n=== DEV RESULTS (M3-M6) ===")
for name, m, lat, tr in results_summary:
    print(f"{name}: acc={m['accuracy']:.4f} prec={m['precision']:.4f} rec={m['recall']:.4f} fpr={m['fpr']:.4f} f1={m['f1']:.4f} auc={m['roc_auc']:.4f} prauc={m['pr_auc']:.4f} brier={m['brier']:.4f} ece={m['ece']:.4f} lat={lat:.3f}ms train={tr:.1f}s")

# Append to summary CSV
summary_df = pd.DataFrame([{
    "model": r[0], "accuracy": r[1]["accuracy"], "precision": r[1]["precision"],
    "recall": r[1]["recall"], "fpr": r[1]["fpr"], "f1": r[1]["f1"],
    "roc_auc": r[1]["roc_auc"], "pr_auc": r[1]["pr_auc"], "brier": r[1]["brier"],
    "ece": r[1]["ece"], "latency_ms": r[2], "train_time_s": r[3],
} for r in results_summary])
existing_path = os.path.join(ROOT, "reports/tables/model_comparison_dev.csv")
if os.path.exists(existing_path):
    old = pd.read_csv(existing_path)
    summary_df = pd.concat([old, summary_df], ignore_index=True)
summary_df.to_csv(existing_path, index=False)
print("Summary saved.")
