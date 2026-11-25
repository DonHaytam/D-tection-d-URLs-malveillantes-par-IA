"""Train and evaluate candidate models on project TRAIN + audited external data.

The deployed model is never overwritten. Candidates are saved under
models/versions/candidates/ and compared on project DEV and external DEV.

Label convention: 0 = legitimate, 1 = phishing.
"""
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
CAND_DIR = os.path.join(ROOT, "models", "versions", "candidates")
EXP_DIR = os.path.join(ROOT, "experiments", "results")
os.makedirs(OUT, exist_ok=True)
os.makedirs(CAND_DIR, exist_ok=True)
os.makedirs(EXP_DIR, exist_ok=True)

AUTH_TOKEN_RE = r"login|signin|sign-in|auth|account|verify|password|oauth|register|signup|security|checkout|payment|billing|secure"

def next_exp_id():
    existing = [f for f in os.listdir(EXP_DIR) if f.startswith("EXP") and f.endswith(".json")]
    nums = []
    for f in existing:
        try:
            nums.append(int(f[3:6]))
        except ValueError:
            pass
    return f"EXP{max(nums, default=0) + 1:03d}"

def evaluate(y, s):
    y = np.asarray(y).astype(int)
    s = np.asarray(s).astype(float)
    met = compute_metrics(y, s, threshold=0.5)
    met["ece"] = expected_calibration_error(y, s)
    fpr, tpr, thr = roc_curve(y, s)
    ok = fpr <= 0.01
    best_thr = float(thr[ok][int(np.argmax(tpr[ok]))]) if ok.any() else 1.0
    met_1pct = compute_metrics(y, s, threshold=best_thr)
    pred3 = np.where(s >= 0.75, 1, np.where(s < 0.25, 0, 2))
    legit = y == 0
    phish = y == 1
    met3 = {
        "phishing_recall": float((pred3[phish] == 1).mean()) if phish.any() else None,
        "phishing_detected_incl_review": float((pred3[phish] >= 1).mean()) if phish.any() else None,
        "legit_fpr": float((pred3[legit] == 1).mean()) if legit.any() else None,
        "review_rate": float((pred3 == 2).mean()),
        "review_rate_legit": float((pred3[legit] == 2).mean()) if legit.any() else None,
        "review_rate_phish": float((pred3[phish] == 2).mean()) if phish.any() else None,
    }
    return {
        "n": int(len(y)),
        "positives": int(phish.sum()),
        "negatives": int(legit.sum()),
        "at_0.5": met,
        "best_threshold_fpr_le_0.01": {"threshold": best_thr, **met_1pct},
        "three_class_0.25_0.75": met3,
    }

def auth_metrics(df, s):
    if "is_auth_path" not in df.columns:
        return {}
    auth = df["is_auth_path"].astype(int).values == 1
    y = df["label"].astype(int).values
    out = {}
    for lab, name in [(0, "legit_auth"), (1, "phish_auth")]:
        mask = auth & (y == lab)
        if mask.any():
            out[name] = {
                "n": int(mask.sum()),
                "mean_score": float(s[mask].mean()),
                "score_ge_0.5": float((s[mask] >= 0.5).mean()),
                "score_ge_0.75": float((s[mask] >= 0.75).mean()),
            }
    return out

# ---------------------------------------------------------------- data
TRAIN = pd.read_csv(os.path.join(ROOT, "data/splits/TRAIN.csv"))
DEV = pd.read_csv(os.path.join(ROOT, "data/splits/DEV.csv"))
EXT_TRAIN = pd.read_csv(os.path.join(ROOT, "data/integrated/external_train.csv"))
EXT_DEV = pd.read_csv(os.path.join(ROOT, "data/integrated/external_dev.csv"))

print(f"TRAIN={len(TRAIN)} DEV={len(DEV)} EXT_TRAIN={len(EXT_TRAIN)} EXT_DEV={len(EXT_DEV)}")
print("EXT_TRAIN labels:", EXT_TRAIN["label"].value_counts().to_dict())

# Baseline scores for hard-example mining (external TRAIN only; never DEV).
base = joblib.load(os.path.join(ROOT, "models/versions/M1_LR_HARDNEG.joblib"))
print("Scoring external TRAIN with baseline for hard-example mining...")
ext_urls = EXT_TRAIN["url"].astype(str).tolist()
ext_scores = base["model"].predict_proba(base["vectorizer"].transform(ext_urls))[:, 1]
EXT_TRAIN = EXT_TRAIN.copy()
EXT_TRAIN["base_score"] = ext_scores
print("External TRAIN base score distribution:",
      {lab: float(EXT_TRAIN.loc[EXT_TRAIN.label == lab, "base_score"].mean()) for lab in [0, 1]})

# Candidate definitions: (name, n_legit, n_phish, mode, C, class_weight, external_weight)
CANDIDATES = [
    ("CLEAN_TRAIN_ONLY", 0, 0, "random", 1.0, "balanced", 1.0),
    ("EXT_RANDOM_40K", 20000, 20000, "random", 1.0, "balanced", 1.0),
    ("EXT_RANDOM_80K", 40000, 40000, "random", 1.0, "balanced", 1.0),
    ("EXT_RANDOM_160K", 80000, 80000, "random", 1.0, "balanced", 1.0),
    ("EXT_HARD_20K", 10000, 10000, "hard", 1.0, "balanced", 1.0),
    ("EXT_HARD_40K", 20000, 20000, "hard", 1.0, "balanced", 1.0),
    ("EXT_RANDOM_160K_W0.5", 80000, 80000, "random", 1.0, "balanced", 0.5),
]

def pick_external(n_legit, n_phish, mode, seed=42):
    rng = np.random.default_rng(seed)
    legit = EXT_TRAIN[EXT_TRAIN["label"] == 0]
    phish = EXT_TRAIN[EXT_TRAIN["label"] == 1]
    if mode == "random":
        l = legit.sample(n=min(n_legit, len(legit)), random_state=seed)
        p = phish.sample(n=min(n_phish, len(phish)), random_state=seed)
        return l, p
    # hard mode: prioritise hard negatives and hard positives, then fill randomly
    hard_l = legit[legit["base_score"] >= 0.5].sort_values("base_score", ascending=False)
    auth_l = legit[legit["url"].str.contains(AUTH_TOKEN_RE, case=False, regex=True)]
    l_parts = [hard_l, auth_l[~auth_l.index.isin(hard_l.index)]]
    l = pd.concat(l_parts) if l_parts else legit.iloc[0:0]
    l = l.drop_duplicates(subset=["url"])
    if len(l) > n_legit:
        l = l.head(n_legit)
    elif len(l) < n_legit:
        rest = legit[~legit.index.isin(l.index)]
        l = pd.concat([l, rest.sample(n=min(n_legit - len(l), len(rest)), random_state=seed)])
    hard_p = phish[phish["base_score"] < 0.5].sort_values("base_score", ascending=True)
    no_auth_p = phish[~phish["url"].str.contains(AUTH_TOKEN_RE, case=False, regex=True)]
    p_parts = [hard_p, no_auth_p[~no_auth_p.index.isin(hard_p.index)]]
    p = pd.concat(p_parts) if p_parts else phish.iloc[0:0]
    p = p.drop_duplicates(subset=["url"])
    if len(p) > n_phish:
        p = p.head(n_phish)
    elif len(p) < n_phish:
        rest = phish[~phish.index.isin(p.index)]
        p = pd.concat([p, rest.sample(n=min(n_phish - len(p), len(rest)), random_state=seed)])
    return l, p

results = {}
for name, n_l, n_p, mode, C, cw, ext_w in CANDIDATES:
    print(f"\n{'='*70}\nTraining {name} (legit={n_l}, phish={n_p}, mode={mode}, C={C}, cw={cw}, ext_w={ext_w})")
    t0 = time.time()
    parts = [TRAIN[["url", "label"]]]
    weights = [np.ones(len(TRAIN), dtype=float)]
    if n_l or n_p:
        l, p = pick_external(n_l, n_p, mode)
        ext = pd.concat([l[["url", "label"]], p[["url", "label"]]], ignore_index=True)
        parts.append(ext)
        weights.append(np.full(len(ext), ext_w, dtype=float))
        print(f"  external used: legit={len(l)} phish={len(p)} total={len(ext)}")
    data = pd.concat(parts, ignore_index=True)
    sw = np.concatenate(weights)
    # shuffle deterministically
    rng = np.random.default_rng(42)
    idx = rng.permutation(len(data))
    data = data.iloc[idx].reset_index(drop=True)
    sw = sw[idx]
    X = data["url"].astype(str).tolist()
    y = data["label"].astype(int).values

    vec = TfidfVectorizer(analyzer="char", ngram_range=(3, 5), min_df=3,
                          max_features=20000, lowercase=True, sublinear_tf=True)
    Xtr = vec.fit_transform(X)
    Xdev = vec.transform(DEV["url"].astype(str).tolist())
    Xext = vec.transform(EXT_DEV["url"].astype(str).tolist())
    print(f"  features={Xtr.shape} fit={time.time()-t0:.1f}s")

    t1 = time.time()
    model = LogisticRegression(C=C, class_weight=cw, solver="saga", max_iter=2000,
                               random_state=42, n_jobs=-1)
    model.fit(Xtr, y, sample_weight=sw)
    train_s = time.time() - t1
    print(f"  trained in {train_s:.1f}s")

    s_dev = model.predict_proba(Xdev)[:, 1]
    s_ext = model.predict_proba(Xext)[:, 1]
    res_dev = evaluate(DEV["label"].values, s_dev)
    res_ext = evaluate(EXT_DEV["label"].values, s_ext)
    res_dev["auth"] = auth_metrics(DEV, s_dev)
    res_ext["auth"] = auth_metrics(EXT_DEV, s_ext)

    results[name] = {
        "config": {"n_legit": n_l, "n_phish": n_p, "mode": mode, "C": C,
                   "class_weight": cw, "external_weight": ext_w,
                   "n_train": int(len(data)), "n_features": int(Xtr.shape[1])},
        "training_time_s": round(train_s, 2),
        "dev": res_dev,
        "external_dev": res_ext,
    }
    m = res_dev["at_0.5"]
    b = res_dev["best_threshold_fpr_le_0.01"]
    t3 = res_dev["three_class_0.25_0.75"]
    print(f"  DEV @0.5: rec={m['recall']:.4f} fpr={m['fpr']:.4f} f1={m['f1']:.4f} auc={m['roc_auc']:.4f}")
    print(f"  DEV @FPR<=1%: thr={b['threshold']:.4f} rec={b['recall']:.4f} fpr={b['fpr']:.4f} prec={b['precision']:.4f}")
    print(f"  DEV 3-class: rec={t3['phishing_recall']:.4f} fpr={t3['legit_fpr']:.4f} review={t3['review_rate']:.4f}")
    me = res_ext["at_0.5"]
    be = res_ext["best_threshold_fpr_le_0.01"]
    print(f"  EXT @0.5: rec={me['recall']:.4f} fpr={me['fpr']:.4f} f1={me['f1']:.4f} auc={me['roc_auc']:.4f}")
    print(f"  EXT @FPR<=1%: rec={be['recall']:.4f} fpr={be['fpr']:.4f}")

    # save candidate artifact + experiment
    art_path = os.path.join(CAND_DIR, f"{name}.joblib")
    joblib.dump({"model": model, "vectorizer": vec}, art_path)
    eid = next_exp_id()
    exp = {
        "experiment_id": eid,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "dataset_version": "v2_external",
        "train_split": "TRAIN" + ("+EXTERNAL_TRAIN" if n_l or n_p else ""),
        "dev_split": "DEV",
        "model_name": name,
        "representation": "char_tfidf_3_5 + audited external URLs",
        "hyperparameters": {"C": C, "class_weight": cw, "external_weight": ext_w,
                            "n_legit_external": n_l, "n_phish_external": n_p, "mode": mode},
        "random_seed": 42,
        "metrics_dev": res_dev["at_0.5"],
        "metrics_dev_fpr_le_0.01": res_dev["best_threshold_fpr_le_0.01"],
        "metrics_dev_three_class": res_dev["three_class_0.25_0.75"],
        "metrics_external_dev": res_ext["at_0.5"],
        "metrics_external_dev_fpr_le_0.01": res_ext["best_threshold_fpr_le_0.01"],
        "training_time_s": round(train_s, 2),
        "model_artifact_path": art_path,
    }
    with open(os.path.join(EXP_DIR, f"{eid}.json"), "w", encoding="utf-8") as f:
        json.dump(exp, f, indent=2, default=str)
    results[name]["experiment_id"] = eid
    results[name]["artifact"] = art_path
    print(f"  saved {eid} -> {art_path}")

    del model, vec, Xtr, Xdev, Xext, data
    gc.collect()

with open(os.path.join(OUT, "model_candidates.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, default=str)
print(f"\nSaved summary: {OUT}/model_candidates.json")

# Compact comparison table
print("\n=== COMPARISON (DEV) ===")
print(f"{'candidate':24s} {'rec@0.5':>8s} {'fpr@0.5':>8s} {'auc':>8s} {'rec@1%':>8s} {'fpr@1%':>8s} {'3c_rec':>8s} {'3c_fpr':>8s}")
for name, r in results.items():
    m = r["dev"]["at_0.5"]; b = r["dev"]["best_threshold_fpr_le_0.01"]; t3 = r["dev"]["three_class_0.25_0.75"]
    print(f"{name:24s} {m['recall']:8.4f} {m['fpr']:8.4f} {m['roc_auc']:8.4f} "
          f"{b['recall']:8.4f} {b['fpr']:8.4f} {t3['phishing_recall']:8.4f} {t3['legit_fpr']:8.4f}")
