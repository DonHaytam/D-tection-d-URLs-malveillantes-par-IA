"""Hybrid experiment: char TF-IDF + numeric/structural + Tranco reputation features.

Tests whether a general domain-reputation feature (Tranco rank) plus auth-path
interactions reduces false positives on legitimate authentication URLs without
hard-coding brands or using an allow-list.
"""
import gc
import json
import os
import re
import sys
import time
import zipfile

sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

import numpy as np
import pandas as pd
import joblib
from scipy.sparse import hstack, csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_curve

from src.evaluation.metrics import compute_metrics, expected_calibration_error
from src.features.feature_pipeline import build_numeric_features
from src.data.provenance import registrable_domain
from src.data.validation import extract_components

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
OUT = os.path.join(ROOT, "reports", "data_expansion_public")
CAND_DIR = os.path.join(ROOT, "models", "versions", "candidates")
EXP_DIR = os.path.join(ROOT, "experiments", "results")
os.makedirs(OUT, exist_ok=True)
os.makedirs(CAND_DIR, exist_ok=True)

AUTH_RE = re.compile(
    r"(?:^|/)(login|signin|sign-in|sign_in|auth|account|accounts|verify|verification|"
    r"password|oauth|register|signup|sign-up|security|checkout|payment|billing|"
    r"wp-login\.php|login\.php|signin\.php)(?:/|$|[.?])", re.I)
AUTH_TOKEN_RE = re.compile(r"login|signin|sign-in|auth|account|verify|password|oauth|register|signup|security|checkout|payment|billing|secure", re.I)

def is_auth_path(u):
    try:
        p = str(u).split("://", 1)[1]
        path = p.split("/", 1)[1] if "/" in p else ""
        return int(bool(AUTH_RE.search("/" + path.split("?")[0])))
    except Exception:
        return 0

def next_exp_id():
    nums = []
    for f in os.listdir(EXP_DIR):
        if f.startswith("EXP") and f.endswith(".json"):
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
    return {
        "n": int(len(y)), "positives": int(phish.sum()), "negatives": int(legit.sum()),
        "at_0.5": met,
        "best_threshold_fpr_le_0.01": {"threshold": best_thr, **met_1pct},
        "three_class_0.25_0.75": {
            "phishing_recall": float((pred3[phish] == 1).mean()) if phish.any() else None,
            "phishing_detected_incl_review": float((pred3[phish] >= 1).mean()) if phish.any() else None,
            "legit_fpr": float((pred3[legit] == 1).mean()) if legit.any() else None,
            "review_rate": float((pred3 == 2).mean()),
        },
    }

def auth_metrics(df, s):
    y = df["label"].astype(int).values
    a = df["auth_path"].astype(int).values == 1
    out = {}
    for lab, name in [(0, "legit_auth"), (1, "phish_auth")]:
        m = a & (y == lab)
        if m.any():
            out[name] = {"n": int(m.sum()), "mean_score": float(s[m].mean()),
                         "score_ge_0.5": float((s[m] >= 0.5).mean()),
                         "score_ge_0.75": float((s[m] >= 0.75).mean())}
    return out

# ---------------------------------------------------------------- Tranco
print("Loading Tranco...")
with zipfile.ZipFile(os.path.join(ROOT, "data/raw/tranco_top1m.csv.zip")) as z:
    with z.open("top-1m.csv") as f:
        tranco = pd.read_csv(f, header=None, names=["rank", "domain"])
tranco_rank = {str(d).lower(): int(r) for r, d in zip(tranco["rank"], tranco["domain"])}
print(f"Tranco domains: {len(tranco_rank)}")

def numeric_frame(urls):
    base = build_numeric_features(urls)
    hosts = []
    rds = []
    auths = []
    toks = []
    for u in urls:
        try:
            host = extract_components(u)["host"]
        except Exception:
            host = ""
        hosts.append(host)
        rds.append(registrable_domain(host))
        auths.append(is_auth_path(u))
        toks.append(len(AUTH_TOKEN_RE.findall(str(u).lower())))
    ranks = np.array([tranco_rank.get(d, 0) for d in rds], dtype=float)
    present = (ranks > 0).astype(float)
    log_rank = np.where(ranks > 0, np.log1p(ranks), 0.0)
    top10k = ((ranks > 0) & (ranks <= 10000)).astype(float)
    top100k = ((ranks > 0) & (ranks <= 100000)).astype(float)
    top1m = present
    auth = np.array(auths, dtype=float)
    tok = np.array(toks, dtype=float)
    extra = pd.DataFrame({
        "tranco_present": present,
        "tranco_log_rank": log_rank,
        "tranco_top10k": top10k,
        "tranco_top100k": top100k,
        "tranco_top1m": top1m,
        "auth_path_flag": auth,
        "auth_token_count": tok,
        "auth_x_top10k": auth * top10k,
        "auth_x_present": auth * present,
        "auth_x_absent": auth * (1.0 - present),
        "token_x_present": tok * present,
        "token_x_absent": tok * (1.0 - present),
    })
    return pd.concat([base.reset_index(drop=True), extra.reset_index(drop=True)], axis=1)

def make_matrices(train_urls, eval_urls, ext_urls=None):
    t0 = time.time()
    vec = TfidfVectorizer(analyzer="char", ngram_range=(3, 5), min_df=3,
                          max_features=20000, lowercase=True, sublinear_tf=True)
    Xtr_char = vec.fit_transform(train_urls)
    Xev_char = vec.transform(eval_urls)
    Xex_char = vec.transform(ext_urls) if ext_urls is not None else None
    print(f"  char fit {time.time()-t0:.1f}s")
    t0 = time.time()
    Ntr = numeric_frame(train_urls)
    Nev = numeric_frame(eval_urls)
    Nex = numeric_frame(ext_urls) if ext_urls is not None else None
    scaler = StandardScaler()
    Ntr_s = scaler.fit_transform(Ntr.values.astype(np.float32))
    Nev_s = scaler.transform(Nev.values.astype(np.float32))
    Nex_s = scaler.transform(Nex.values.astype(np.float32)) if Nex is not None else None
    print(f"  numeric {Ntr.shape} fit {time.time()-t0:.1f}s")
    Xtr = hstack([Xtr_char, csr_matrix(Ntr_s)]).tocsr()
    Xev = hstack([Xev_char, csr_matrix(Nev_s)]).tocsr()
    Xex = hstack([Xex_char, csr_matrix(Nex_s)]).tocsr() if Nex_s is not None else None
    return vec, scaler, list(Ntr.columns), Xtr, Xev, Xex

TRAIN = pd.read_csv(os.path.join(ROOT, "data/splits/TRAIN.csv"))
DEV = pd.read_csv(os.path.join(ROOT, "data/splits/DEV.csv"))
EXT_TRAIN = pd.read_csv(os.path.join(ROOT, "data/integrated/external_train.csv"))
EXT_DEV = pd.read_csv(os.path.join(ROOT, "data/integrated/external_dev.csv"))
for df in (TRAIN, DEV, EXT_TRAIN, EXT_DEV):
    df["auth_path"] = df["url"].map(is_auth_path)

# Balanced external sample for the hybrid-with-external candidate.
rng = np.random.default_rng(42)
legit = EXT_TRAIN[EXT_TRAIN["label"] == 0]
phish = EXT_TRAIN[EXT_TRAIN["label"] == 1]
ext_sample = pd.concat([
    legit.sample(n=20000, random_state=42),
    phish.sample(n=20000, random_state=42),
], ignore_index=True)
print(f"External sample: {len(ext_sample)} ({ext_sample.label.value_counts().to_dict()})")

CONFIGS = [
    ("HYBRID_TRAIN", "train", 1.0, "balanced"),
    ("HYBRID_EXT40K", "ext", 1.0, "balanced"),
]
results = {}
for name, mode, C, cw in CONFIGS:
    print(f"\n{'='*70}\n{name} mode={mode} C={C} cw={cw}")
    if mode == "train":
        tr = TRAIN[["url", "label"]]
    else:
        tr = pd.concat([TRAIN[["url", "label"]], ext_sample[["url", "label"]]], ignore_index=True)
    tr = tr.sample(frac=1.0, random_state=42).reset_index(drop=True)
    Xtr_urls = tr["url"].astype(str).tolist()
    ytr = tr["label"].astype(int).values
    Xev_urls = DEV["url"].astype(str).tolist()
    Xex_urls = EXT_DEV["url"].astype(str).tolist()
    vec, scaler, num_names, Xtr, Xev, Xex = make_matrices(Xtr_urls, Xev_urls, Xex_urls)
    t0 = time.time()
    model = LogisticRegression(C=C, class_weight=cw, solver="lbfgs", max_iter=300,
                               tol=1e-3, random_state=42, n_jobs=-1)
    model.fit(Xtr, ytr)
    tr_time = time.time() - t0
    s_dev = model.predict_proba(Xev)[:, 1]
    s_ext = model.predict_proba(Xex)[:, 1]
    res_dev = evaluate(DEV["label"].values, s_dev)
    res_ext = evaluate(EXT_DEV["label"].values, s_ext)
    res_dev["auth"] = auth_metrics(DEV, s_dev)
    res_ext["auth"] = auth_metrics(EXT_DEV, s_ext)
    results[name] = {"config": {"mode": mode, "C": C, "class_weight": cw,
                                "n_train": int(len(tr)), "n_features": int(Xtr.shape[1])},
                     "training_time_s": round(tr_time, 2),
                     "dev": res_dev, "external_dev": res_ext}
    m = res_dev["at_0.5"]; b = res_dev["best_threshold_fpr_le_0.01"]; t3 = res_dev["three_class_0.25_0.75"]
    print(f"  DEV @0.5: rec={m['recall']:.4f} fpr={m['fpr']:.4f} f1={m['f1']:.4f} auc={m['roc_auc']:.4f}")
    print(f"  DEV @FPR<=1%: thr={b['threshold']:.4f} rec={b['recall']:.4f} fpr={b['fpr']:.4f}")
    print(f"  DEV 3-class: rec={t3['phishing_recall']:.4f} fpr={t3['legit_fpr']:.4f}")
    print(f"  DEV legit_auth: {res_dev['auth'].get('legit_auth')}")
    me = res_ext["at_0.5"]; be = res_ext["best_threshold_fpr_le_0.01"]
    print(f"  EXT @0.5: rec={me['recall']:.4f} fpr={me['fpr']:.4f} auc={me['roc_auc']:.4f}")
    print(f"  EXT @FPR<=1%: rec={be['recall']:.4f} fpr={be['fpr']:.4f}")

    art_path = os.path.join(CAND_DIR, f"{name}.joblib")
    joblib.dump({"model": model, "vectorizer": vec, "scaler": scaler,
                 "numeric_feature_names": num_names, "kind": "hybrid_char_numeric"}, art_path)
    eid = next_exp_id()
    exp = {"experiment_id": eid, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "dataset_version": "v2_hybrid", "train_split": mode, "dev_split": "DEV",
           "model_name": name, "representation": "char_tfidf_3_5 + numeric/structural + Tranco reputation",
           "hyperparameters": {"C": C, "class_weight": cw}, "random_seed": 42,
           "metrics_dev": res_dev["at_0.5"],
           "metrics_dev_fpr_le_0.01": res_dev["best_threshold_fpr_le_0.01"],
           "metrics_dev_three_class": res_dev["three_class_0.25_0.75"],
           "metrics_external_dev": res_ext["at_0.5"],
           "training_time_s": round(tr_time, 2), "model_artifact_path": art_path}
    with open(os.path.join(EXP_DIR, f"{eid}.json"), "w", encoding="utf-8") as f:
        json.dump(exp, f, indent=2, default=str)
    results[name]["experiment_id"] = eid
    results[name]["artifact"] = art_path
    print(f"  saved {eid}")
    del model, vec, scaler, Xtr, Xev, Xex
    gc.collect()

with open(os.path.join(OUT, "hybrid_candidates.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, default=str)

print("\n=== HYBRID COMPARISON (DEV) ===")
for name, r in results.items():
    m = r["dev"]["at_0.5"]; b = r["dev"]["best_threshold_fpr_le_0.01"]; t3 = r["dev"]["three_class_0.25_0.75"]
    print(f"{name:20s} rec@0.5={m['recall']:.4f} fpr@0.5={m['fpr']:.4f} auc={m['roc_auc']:.4f} "
          f"rec@1%={b['recall']:.4f} fpr@1%={b['fpr']:.4f} 3c_rec={t3['phishing_recall']:.4f} 3c_fpr={t3['legit_fpr']:.4f}")
