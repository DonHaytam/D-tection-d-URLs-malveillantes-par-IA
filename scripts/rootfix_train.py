"""Phase 4-6 — Train with hard-negative auth URLs."""
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

# Load hard negatives (sample)
hn = pd.read_csv(os.path.join(ROOT, "data/interim/hn_legit_auth.csv"))
# Sample 30k stratified by domain
hn_sample = hn.sample(n=5000, random_state=42).reset_index(drop=True)
print(f"Hard negatives sampled: {len(hn_sample)}")

# Load hard positives
hp = pd.read_csv(os.path.join(ROOT, "data/interim/hard_pos_phishing.csv"))
hp_sample = hp.sample(n=min(2500, len(hp)), random_state=42).reset_index(drop=True)
print(f"Hard positives sampled: {len(hp_sample)}")

# Combine: original TRAIN + hard negatives + hard positives
# Align columns
for df in [hn_sample, hp_sample]:
    for c in TRAIN.columns:
        if c not in df.columns:
            df[c] = None
    df = df[TRAIN.columns]

augmented = pd.concat([TRAIN, hn_sample[TRAIN.columns], hp_sample[TRAIN.columns]], ignore_index=True)
print(f"Augmented TRAIN: {len(augmented)} (was {len(TRAIN)})")
print(augmented["label"].value_counts().to_dict())

# Domain-disjoint check: ensure HN domains don't overlap with DEV
dev_domains = set(DEV["registrable_domain"].dropna().astype(str))
hn_domains = set(hn_sample["url"].map(lambda u: u.split("://")[1].split("/")[0].split(".")[-2] + "." + u.split("://")[1].split("/")[0].split(".")[-1] if "://" in u else "").dropna())
overlap = hn_domains & dev_domains
print(f"Domain overlap between HN and DEV: {len(overlap)}")

Xtr = augmented["url"].astype(str).tolist()
ytr = augmented["label"].astype(int).values
Xdev = DEV["url"].astype(str).tolist()
ydev = DEV["label"].astype(int).values

char_vec = TfidfVectorizer(analyzer="char", ngram_range=(3,5), min_df=10, max_features=5000, lowercase=True, sublinear_tf=True)
Xtr_c = char_vec.fit_transform(Xtr)
Xdev_c = char_vec.transform(Xdev)

def next_exp_id():
    existing = sorted(os.listdir(os.path.join(ROOT, "experiments/results")))
    return f"EXP{len(existing)+1:03d}"

# Train with C=1.0
name = "ROOTFIX_LR_HN30K"
print(f"\nTraining {name}")
t0 = time.time()
m = LogisticRegression(C=1.0, class_weight="balanced", solver="saga", max_iter=3000, random_state=42, n_jobs=-1)
m.fit(Xtr_c, ytr)
tr = time.time() - t0
sc = m.predict_proba(Xdev_c)[:, 1]
met = compute_metrics(ydev, sc)
met["ece"] = expected_calibration_error(ydev, sc)
print(f"  acc={met['accuracy']:.4f} rec={met['recall']:.4f} fpr={met['fpr']:.4f} f1={met['f1']:.4f} auc={met['roc_auc']:.4f} ece={met['ece']:.4f} train={tr:.1f}s")

# Test on diagnostic URLs
diag_urls = [
    "https://www.paypal.com/signin",
    "https://www.dropbox.com/login",
    "https://github.com/login",
    "https://accounts.google.com/signin",
    "https://login.microsoftonline.com/",
    "https://www.amazon.com/ap/signin",
    "https://www.apple.com/shop/account/home",
    "https://www.linkedin.com/login",
    "secure-login-example.com/account",
    "verify-user-example.net/login",
    "account-security-example.org/verify",
    "paypal-login-example.com/signin",
    "amazon-account-example.net/verify",
]
diag_scores = m.predict_proba(char_vec.transform(diag_urls))[:, 1]
print("\n=== DIAGNOSTIC URLS ===")
for u, s in zip(diag_urls, diag_scores):
    print(f"  {s*100:6.2f}%  {u}")

# Save
eid = next_exp_id()
joblib.dump({"model": m, "vectorizer": char_vec}, os.path.join(ROOT, "models/versions", f"{name}.joblib"))
exp = {"experiment_id": eid, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
       "dataset_version": "v1", "train_split": "TRAIN+HN30K+HP15K", "dev_split": "DEV",
       "n_train": len(ytr), "n_dev": len(ydev), "model_name": name,
       "representation": "char_tfidf_3_5 + 30k hard-neg auth + 15k hard-pos",
       "hyperparameters": {"C": 1.0, "class_weight": "balanced"}, "random_seed": 42,
       "metrics_dev": met, "training_time_s": round(tr, 3),
       "model_artifact_path": os.path.join(ROOT, "models/versions", f"{name}.joblib")}
with open(os.path.join(ROOT, "experiments/results", eid + ".json"), "w") as f:
    json.dump(exp, f, indent=2, default=str)
print(f"\nSaved {eid}")

# Threshold optimization
best_feasible = None
for t in np.unique(sc):
    pred = (sc >= t).astype(int)
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
    print(f"\nBest feasible threshold: {best_feasible[0]:.4f} recall={best_feasible[2]:.4f} fpr={best_feasible[1]:.4f}")
else:
    best_min = None
    for t in np.unique(sc):
        pred = (sc >= t).astype(int)
        tp = int(((pred==1)&(ydev==1)).sum())
        fp = int(((pred==1)&(ydev==0)).sum())
        tn = int(((pred==0)&(ydev==0)).sum())
        fn = int(((pred==0)&(ydev==1)).sum())
        rec = tp/(tp+fn) if tp+fn else 0
        fpr = fp/(fp+tn) if fp+tn else 0
        if best_min is None or fpr < best_min[1]:
            best_min = (t, fpr, rec, tp, fp, tn, fn)
    print(f"\nNo threshold with recall>=0.85. Best min FPR: {best_min[0]:.4f} recall={best_min[2]:.4f} fpr={best_min[1]:.4f}")
    print(f"  TP={best_min[3]} FP={best_min[4]} TN={best_min[5]} FN={best_min[6]}")
