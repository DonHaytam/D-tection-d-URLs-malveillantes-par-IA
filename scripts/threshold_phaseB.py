"""Phase B — Threshold optimization for all models on DEV."""
import sys, os, json
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

import numpy as np
import pandas as pd
import joblib
from src.evaluation.threshold_optimizer import optimize_thresholds, bootstrap_threshold_stability

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
DEV = pd.read_csv(os.path.join(ROOT, "data/splits/DEV.csv"))
ydev = DEV["label"].astype(int).values
Xdev_url = DEV["url"].astype(str).tolist()

from src.features.feature_pipeline import build_numeric_features
Xdev_num = build_numeric_features(Xdev_url)

models = {
    "M1_LR": ("text", joblib.load(os.path.join(ROOT, "models/versions/M1_LR.joblib"))),
    "M2_SVM": ("text", joblib.load(os.path.join(ROOT, "models/versions/M2_SVM.joblib"))),
    "M3_RF": ("num", joblib.load(os.path.join(ROOT, "models/versions/M3_RF.joblib"))),
    "M4_GB": ("num", joblib.load(os.path.join(ROOT, "models/versions/M4_GB.joblib"))),
    "M5_XGBOOST": ("num", joblib.load(os.path.join(ROOT, "models/versions/M5_XGBOOST.joblib"))),
}

# M6 hybrid
hybrid_art = joblib.load(os.path.join(ROOT, "models/versions/M6_HYBRID.joblib"))
models["M6_HYBRID"] = ("hybrid", hybrid_art)

all_results = []
for name, (kind, art) in models.items():
    model = art["model"]
    if kind == "text":
        vec = art["vectorizer"]
        sc = model.predict_proba(vec.transform(Xdev_url))[:, 1]
    elif kind == "num":
        fnames = art["feature_names"]
        X = Xdev_num[fnames]
        sc = model.predict_proba(X)[:, 1]
    else:
        sc = model.predict_proba(Xdev_url)[:, 1]
    df_thr, best = optimize_thresholds(ydev, sc, target_recall=0.85)
    boot = bootstrap_threshold_stability(ydev, sc, target_recall=0.85, n_boot=100)
    feasible = df_thr[df_thr["recall"] >= 0.85]
    print(f"\n{name}: best feasible threshold={best['threshold']:.4f} recall={best['recall']:.4f} fpr={best['fpr']:.4f} prec={best['precision']:.4f}")
    print(f"  bootstrap thr: mean={boot['mean']:.4f} std={boot['std']:.4f} [{boot['q025']:.4f}, {boot['q975']:.4f}]")
    all_results.append({"model": name, "threshold": best["threshold"], "recall": best["recall"],
                        "fpr": best["fpr"], "precision": best["precision"],
                        "tp": int(best["tp"]), "fp": int(best["fp"]), "tn": int(best["tn"]), "fn": int(best["fn"]),
                        "boot_mean": boot["mean"], "boot_std": boot["std"]})
    df_thr.to_csv(os.path.join(ROOT, "reports/tables", f"thresholds_{name}.csv"), index=False)

res_df = pd.DataFrame(all_results)
res_df.to_csv(os.path.join(ROOT, "reports/tables/threshold_results.csv"), index=False)
print("\n=== THRESHOLD RESULTS ===")
print(res_df.to_string(index=False))
print("\nSaved threshold_results.csv")
