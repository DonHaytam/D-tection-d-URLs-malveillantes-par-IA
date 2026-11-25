"""Phase: Train model with keyword position + brand impersonation features."""
import sys, os, json, time
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

import numpy as np
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from src.evaluation.metrics import compute_metrics, expected_calibration_error
from src.features.feature_pipeline import build_numeric_features
from src.features.keyword_position_features import keyword_position_features
from src.features.brand_impersonation_features import brand_impersonation_features

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
TRAIN = pd.read_csv(os.path.join(ROOT, "data/splits/TRAIN.csv"))
DEV = pd.read_csv(os.path.join(ROOT, "data/splits/DEV.csv"))
Xtr = TRAIN["url"].astype(str).tolist()
ytr = TRAIN["label"].astype(int).values
Xdev = DEV["url"].astype(str).tolist()
ydev = DEV["label"].astype(int).values

def build_enhanced(urls):
    base = build_numeric_features(urls)
    kw = pd.DataFrame([keyword_position_features(u) for u in urls])
    brand = pd.DataFrame([brand_impersonation_features(u) for u in urls])
    return pd.concat([base, kw, brand], axis=1)

print("Building enhanced features...")
Xtr_num = build_enhanced(Xtr)
Xdev_num = build_enhanced(Xdev)
print("shape:", Xtr_num.shape)
feat_names = list(Xtr_num.columns)
joblib.dump(feat_names, os.path.join(ROOT, "models/versions", "enhanced_v2_feature_names.joblib"))

# Char TF-IDF
char_vec = TfidfVectorizer(analyzer="char", ngram_range=(3,5), min_df=3, max_features=20000, lowercase=True, sublinear_tf=True)
Xtr_char = char_vec.fit_transform(Xtr)
Xdev_char = char_vec.transform(Xdev)

# Combine
from scipy.sparse import hstack, csr_matrix
Xtr_comb = hstack([Xtr_char, csr_matrix(Xtr_num.values)])
Xdev_comb = hstack([Xdev_char, csr_matrix(Xdev_num.values)])
print("combined shape:", Xtr_comb.shape)

def next_exp_id():
    existing = sorted(os.listdir(os.path.join(ROOT, "experiments/results")))
    return f"EXP{len(existing)+1:03d}"

# Train with various C
best = None
for C in [0.5, 1.0, 2.0]:
    name = f"KP_BI_LR_C{C}"
    print(f"\nTraining {name}")
    t0 = time.time()
    m = LogisticRegression(C=C, class_weight="balanced", solver="saga", max_iter=3000, random_state=42, n_jobs=-1)
    m.fit(Xtr_comb, ytr)
    tr = time.time() - t0
    sc = m.predict_proba(Xdev_comb)[:, 1]
    met = compute_metrics(ydev, sc)
    met["ece"] = expected_calibration_error(ydev, sc)
    print(f"  acc={met['accuracy']:.4f} rec={met['recall']:.4f} fpr={met['fpr']:.4f} f1={met['f1']:.4f} auc={met['roc_auc']:.4f} ece={met['ece']:.4f} train={tr:.1f}s")
    if best is None or met["fpr"] < best[1]["fpr"]:
        best = (name, met, m, C, tr)
    eid = next_exp_id()
    joblib.dump({"model": m, "vectorizer": char_vec, "feature_names": feat_names},
                os.path.join(ROOT, "models/versions", f"{name}.joblib"))
    exp = {"experiment_id": eid, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "dataset_version": "v1", "train_split": "TRAIN", "dev_split": "DEV",
           "n_train": len(ytr), "n_dev": len(ydev), "model_name": name,
           "representation": "char_tfidf + keyword_position + brand_impersonation",
           "hyperparameters": {"C": C, "class_weight": "balanced"}, "random_seed": 42,
           "metrics_dev": met, "training_time_s": round(tr, 3),
           "model_artifact_path": os.path.join(ROOT, "models/versions", f"{name}.joblib")}
    with open(os.path.join(ROOT, "experiments/results", eid + ".json"), "w") as f:
        json.dump(exp, f, indent=2, default=str)
    print(f"  Saved {eid}")

best_name, best_met, best_model, best_C, best_tr = best
joblib.dump({"model": best_model, "vectorizer": char_vec, "feature_names": feat_names},
            os.path.join(ROOT, "models/versions/KP_BI_BEST.joblib"))
print(f"\nBEST: {best_name} fpr={best_met['fpr']:.4f} rec={best_met['recall']:.4f} auc={best_met['roc_auc']:.4f}")

# Threshold optimization for best model
sc_best = best_model.predict_proba(Xdev_comb)[:, 1]
best_feasible = None
for t in np.unique(sc_best):
    pred = (sc_best >= t).astype(int)
    tp = int(((pred==1)&(ydev==1)).sum())
    fp = int(((pred==1)&(ydev==0)).sum())
    tn = int(((pred==0)&(ydev==0)).sum())
    fn = int(((pred==0)&(ydev==1)).sum())
    rec = tp/(tp+fn) if tp+fn else 0
    fpr = fp/(fp+tn) if fp+tn else 0
    if rec >= 0.85:
        if best_feasible is None or fpr < best_feasible[1]:
            best_feasible = (t, fpr, rec, tp, fp, tn, fn)
if best_feasible:
    print(f"Best feasible threshold: {best_feasible[0]:.4f} recall={best_feasible[2]:.4f} fpr={best_feasible[1]:.4f}")
else:
    # Find min FPR
    best_min = None
    for t in np.unique(sc_best):
        pred = (sc_best >= t).astype(int)
        tp = int(((pred==1)&(ydev==1)).sum())
        fp = int(((pred==1)&(ydev==0)).sum())
        tn = int(((pred==0)&(ydev==0)).sum())
        fn = int(((pred==0)&(ydev==1)).sum())
        rec = tp/(tp+fn) if tp+fn else 0
        fpr = fp/(fp+tn) if fp+tn else 0
        if best_min is None or fpr < best_min[1]:
            best_min = (t, fpr, rec, tp, fp, tn, fn)
    print(f"No threshold with recall>=0.85. Best min FPR: {best_min[0]:.4f} recall={best_min[2]:.4f} fpr={best_min[1]:.4f}")
