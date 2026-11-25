"""Phase D/E — Train enhanced-feature models and tune regularization."""
import sys, os, json, time
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

import numpy as np
import pandas as pd
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from src.features.feature_pipeline import build_numeric_features
from src.features.enhanced_lexical_features import enhanced_lexical_features, brand_position_features
from src.evaluation.metrics import compute_metrics, expected_calibration_error

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
TRAIN = pd.read_csv(os.path.join(ROOT, "data/splits/TRAIN.csv"))
DEV = pd.read_csv(os.path.join(ROOT, "data/splits/DEV.csv"))
Xtr_url = TRAIN["url"].astype(str).tolist()
ytr = TRAIN["label"].astype(int).values
Xdev_url = DEV["url"].astype(str).tolist()
ydev = DEV["label"].astype(int).values

def build_enhanced_numeric(urls):
    base = build_numeric_features(urls)
    brand = pd.DataFrame([brand_position_features(u) for u in urls])
    return pd.concat([base, brand], axis=1)

print("Building enhanced numeric features...")
Xtr = build_enhanced_numeric(Xtr_url)
Xdev = build_enhanced_numeric(Xdev_url)
print("shape", Xtr.shape)
feat_names = list(Xtr.columns)
joblib.dump(feat_names, os.path.join(ROOT, "models/versions", "enhanced_feature_names.joblib"))

def next_exp_id():
    existing = sorted(os.listdir(os.path.join(ROOT, "experiments/results")))
    return f"EXP{len(existing)+1:03d}"

# Try multiple configurations
configs = [
    {"name": "M7_LR_ENHANCED", "C": 1.0, "class_weight": "balanced", "penalty": "l2"},
    {"name": "M7_LR_ENHANCED_C0.5", "C": 0.5, "class_weight": "balanced", "penalty": "l2"},
    {"name": "M7_LR_ENHANCED_C0.1", "C": 0.1, "class_weight": "balanced", "penalty": "l2"},
    {"name": "M7_LR_ENHANCED_none", "C": 1.0, "class_weight": None, "penalty": "l2"},
]

results = []
for cfg in configs:
    name = cfg["name"]
    print(f"\nTraining {name} (C={cfg['C']}, cw={cfg['class_weight']})")
    t0 = time.time()
    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(C=cfg["C"], penalty=cfg["penalty"],
                                   class_weight=cfg["class_weight"], solver="saga",
                                   max_iter=2000, random_state=42, n_jobs=-1)),
    ])
    pipe.fit(Xtr, ytr)
    tr_time = time.time() - t0
    sc = pipe.predict_proba(Xdev)[:, 1]
    m = compute_metrics(ydev, sc)
    m["ece"] = expected_calibration_error(ydev, sc)
    print(f"  acc={m['accuracy']:.4f} rec={m['recall']:.4f} fpr={m['fpr']:.4f} f1={m['f1']:.4f} auc={m['roc_auc']:.4f} ece={m['ece']:.4f} train={tr_time:.1f}s")
    mpath = os.path.join(ROOT, "models/versions", f"{name}.joblib")
    joblib.dump({"model": pipe, "feature_names": feat_names}, mpath)
    eid = next_exp_id()
    exp = {"experiment_id": eid, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "dataset_version": "v1", "train_split": "TRAIN", "dev_split": "DEV",
           "n_train": len(ytr), "n_dev": len(ydev), "model_name": name,
           "representation": "enhanced_numeric (lexical+structural+brand_position)",
           "hyperparameters": {"C": cfg["C"], "class_weight": cfg["class_weight"], "penalty": cfg["penalty"]},
           "random_seed": 42, "metrics_dev": m,
           "training_time_s": round(tr_time, 3), "model_artifact_path": mpath}
    with open(os.path.join(ROOT, "experiments/results", eid + ".json"), "w") as f:
        json.dump(exp, f, indent=2, default=str)
    print(f"  Saved {eid}")
    results.append((name, m, tr_time))

print("\n=== Enhanced LR Results ===")
for name, m, tr in results:
    print(f"{name}: acc={m['accuracy']:.4f} rec={m['recall']:.4f} fpr={m['fpr']:.4f} f1={m['f1']:.4f} auc={m['roc_auc']:.4f} ece={m['ece']:.4f}")
