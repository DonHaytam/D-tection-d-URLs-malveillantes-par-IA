"""Phase: Comprehensive improvement — clean data + domain reputation features + hybrid model."""
import sys, os, json, time
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

import numpy as np
import pandas as pd
import joblib
import zipfile
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.preprocessing import FunctionTransformer
from src.evaluation.metrics import compute_metrics, expected_calibration_error
from src.features.feature_pipeline import build_numeric_features
from src.features.enhanced_lexical_features import brand_position_features

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
TRAIN = pd.read_csv(os.path.join(ROOT, "data/splits/TRAIN.csv"))
DEV = pd.read_csv(os.path.join(ROOT, "data/splits/DEV.csv"))

# ---- Load Tranco ranks ----
with zipfile.ZipFile(os.path.join(ROOT, "data/raw/tranco_top1m.csv.zip")) as z:
    with z.open("top-1m.csv") as f:
        tranco = pd.read_csv(f, header=None, names=["rank", "domain"])
tranco_map = dict(zip(tranco["domain"].astype(str).str.lower(), tranco["rank"]))

def tranco_rank_feature(urls):
    ranks = []
    for u in urls:
        host = u.split("://")[-1].split("/")[0].split(":")[0].lower() if "://" in u else u.split("/")[0].split(":")[0].lower()
        parts = host.split(".")
        reg = ".".join(parts[-2:]) if len(parts) >= 2 else host
        r = tranco_map.get(host, tranco_map.get(reg, 1000001))
        # log rank (lower = more popular)
        ranks.append(np.log1p(r))
    return np.array(ranks).reshape(-1, 1)

# ---- Clean TRAIN: remove cross-label domains ----
print("Original TRAIN:", len(TRAIN))
# find domains that appear with both labels in the full manifest
manifest = pd.read_csv(os.path.join(ROOT, "data/processed/manifest_v1.csv"))
cross_domains = set()
dom_labels = manifest.groupby("registrable_domain")["label"].nunique()
cross_domains = set(dom_labels[dom_labels > 1].index)
print("Cross-label domains:", len(cross_domains))
train_clean = TRAIN[~TRAIN["registrable_domain"].isin(cross_domains)].copy()
print("TRAIN after removing cross-label domains:", len(train_clean))

Xtr_url = train_clean["url"].astype(str).tolist()
ytr = train_clean["label"].astype(int).values
Xdev_url = DEV["url"].astype(str).tolist()
ydev = DEV["label"].astype(int).values

# ---- Build features ----
def build_all_features(urls):
    base = build_numeric_features(urls)
    brand = pd.DataFrame([brand_position_features(u) for u in urls])
    tranco_r = tranco_rank_feature(urls)
    tranco_df = pd.DataFrame({"tranco_log_rank": tranco_r.ravel()})
    return pd.concat([base, brand, tranco_df], axis=1)

print("Building features...")
Xtr_num = build_all_features(Xtr_url)
Xdev_num = build_all_features(Xdev_url)
print("shape:", Xtr_num.shape)

# ---- Char TF-IDF ----
char_vec = TfidfVectorizer(analyzer="char", ngram_range=(3,5), min_df=3,
                           max_features=20000, lowercase=True, sublinear_tf=True)
Xtr_char = char_vec.fit_transform(Xtr_url)
Xdev_char = char_vec.transform(Xdev_url)

# ---- Hybrid: char TF-IDF + numeric (with tranco rank + brand position) ----
def numeric_transform(urls):
    return build_all_features(urls).values

from sklearn.preprocessing import FunctionTransformer
numeric_tf = FunctionTransformer(numeric_transform, validate=False)
char_tf = char_vec
features = FeatureUnion([("char", char_tf), ("num", numeric_tf)])

# We need to fit char separately since FeatureUnion with a fitted vectorizer won't refit
# Instead, use a Pipeline with a custom approach: fit vectorizer, then combine
# Approach: transform char with fitted vec, hstack with numeric
from scipy.sparse import hstack, csr_matrix

Xtr_combined = hstack([Xtr_char, csr_matrix(Xtr_num.values)])
Xdev_combined = hstack([Xdev_char, csr_matrix(Xdev_num.values)])
print("combined shape:", Xtr_combined.shape)

# ---- Train LR with various C ----
def next_exp_id():
    existing = sorted(os.listdir(os.path.join(ROOT, "experiments/results")))
    return f"EXP{len(existing)+1:03d}"

best = None
for C in [0.5, 1.0, 2.0]:
    for cw in ["balanced", None]:
        name = f"M8_HYBRID_C{C}_{'bal' if cw else 'none'}"
        print(f"\nTraining {name}")
        t0 = time.time()
        m = LogisticRegression(C=C, class_weight=cw, solver="saga", max_iter=2000,
                               random_state=42, n_jobs=-1)
        m.fit(Xtr_combined, ytr)
        tr_time = time.time() - t0
        sc = m.predict_proba(Xdev_combined)[:, 1]
        met = compute_metrics(ydev, sc)
        met["ece"] = expected_calibration_error(ydev, sc)
        print(f"  acc={met['accuracy']:.4f} rec={met['recall']:.4f} fpr={met['fpr']:.4f} f1={met['f1']:.4f} auc={met['roc_auc']:.4f} ece={met['ece']:.4f} train={tr_time:.1f}s")
        if best is None or met["fpr"] < best[1]["fpr"]:
            best = (name, met, m, C, cw, tr_time)
        # save each
        eid = next_exp_id()
        joblib.dump({"model": m, "vectorizer": char_vec, "feature_names": list(Xtr_num.columns)},
                    os.path.join(ROOT, "models/versions", f"{name}.joblib"))
        exp = {"experiment_id": eid, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "dataset_version": "v1", "train_split": "TRAIN (cross-label removed)", "dev_split": "DEV",
               "n_train": len(ytr), "n_dev": len(ydev), "model_name": name,
               "representation": "char_tfidf + numeric (tranco_rank + brand_position) + cleaned data",
               "hyperparameters": {"C": C, "class_weight": cw}, "random_seed": 42,
               "metrics_dev": met, "training_time_s": round(tr_time, 3),
               "model_artifact_path": os.path.join(ROOT, "models/versions", f"{name}.joblib")}
        with open(os.path.join(ROOT, "experiments/results", eid + ".json"), "w") as f:
            json.dump(exp, f, indent=2, default=str)
        print(f"  Saved {eid}")

print(f"\nBEST: {best[0]} fpr={best[1]['fpr']:.4f} rec={best[1]['recall']:.4f} auc={best[1]['roc_auc']:.4f}")
joblib.dump({"model": best[2], "vectorizer": char_vec, "feature_names": list(Xtr_num.columns)},
            os.path.join(ROOT, "models/versions/M8_BEST_HYBRID.joblib"))
print("Saved M8_BEST_HYBRID.joblib")
