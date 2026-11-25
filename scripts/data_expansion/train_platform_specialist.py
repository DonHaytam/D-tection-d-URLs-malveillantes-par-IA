"""Two-branch platform specialist prototype.

Full-URL model for ordinary domains + a path-focused model for shared
platforms (free hosts, shorteners, document hosts, cloud buckets), where the
registrable-domain reputation is not informative about the individual page.

Training uses only TRAIN and EXTERNAL_TRAIN.  DEV is used only for evaluation.
"""
import gc
import json
import os
import re
import sys
import time

sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master/scripts/data_expansion")

import numpy as np
import pandas as pd
import joblib
from scipy.sparse import hstack, csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_curve, roc_auc_score

from src.evaluation.metrics import compute_metrics, expected_calibration_error
from hybrid_features import load_tranco_rank
from platform_shared import platform_frame, platform_of, platform_numeric, url_path

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
OUT = os.path.join(ROOT, "reports", "data_expansion_public")
CAND = os.path.join(ROOT, "models", "versions", "candidates")
EXP = os.path.join(ROOT, "experiments", "results")


def evaluate(y, s):
    m = compute_metrics(y, s, threshold=0.5)
    m["ece"] = expected_calibration_error(y, s)
    fpr, tpr, thr = roc_curve(y, s)
    out = {"at_0.5": m,
           "at_0.75": compute_metrics(y, s, threshold=0.75),
           "at_0.9": compute_metrics(y, s, threshold=0.9)}
    for target in [0.005, 0.01, 0.02, 0.03, 0.05]:
        ok = fpr <= target
        if ok.any():
            t = float(thr[ok][int(np.argmax(tpr[ok]))])
            out[f"at_fpr_le_{target}"] = {"threshold": t, **compute_metrics(y, s, threshold=t)}
    return out


def next_exp_id():
    nums = []
    for f in os.listdir(EXP):
        if f.startswith("EXP") and f.endswith(".json"):
            try:
                nums.append(int(f[3:6]))
            except ValueError:
                pass
    return f"EXP{max(nums, default=0) + 1:03d}"


TRAIN = pd.read_csv(os.path.join(ROOT, "data/splits/TRAIN.csv"), usecols=["url", "label"])
DEV = pd.read_csv(os.path.join(ROOT, "data/splits/DEV.csv"), usecols=["url", "label"])
EXT_TRAIN = pd.read_csv(os.path.join(ROOT, "data/integrated/external_train.csv"), usecols=["url", "label"])
EXT_DEV = pd.read_csv(os.path.join(ROOT, "data/integrated/external_dev.csv"), usecols=["url", "label"])
for df in (TRAIN, DEV, EXT_TRAIN, EXT_DEV):
    df["platform"] = df["url"].map(lambda u: platform_of(u)[0])
    df["path"] = df["url"].map(url_path)

ptrain = pd.concat([
    TRAIN[TRAIN.platform != ""],
    EXT_TRAIN[EXT_TRAIN.platform != ""],
], ignore_index=True)
print(f"platform train rows={len(ptrain)} by type/label=")
print(pd.crosstab(ptrain.platform, ptrain.label).to_string())
print(f"DEV platform rows={int((DEV.platform != '').sum())}, "
      f"EXT_DEV platform rows={int((EXT_DEV.platform != '').sum())}")

print("Fitting platform path TF-IDF...")
t0 = time.time()
pvec = TfidfVectorizer(analyzer="char", ngram_range=(2, 5), min_df=2, max_features=20000,
                       lowercase=True, sublinear_tf=True, dtype=np.float32)
Ptr_char = pvec.fit_transform(ptrain["path"].tolist())
print(f"  done {time.time()-t0:.1f}s shape={Ptr_char.shape}")
Ntr = platform_numeric(ptrain["url"].tolist())
pcols = list(Ntr.columns)
pscaler = StandardScaler()
Ptr = hstack([Ptr_char, csr_matrix(pscaler.fit_transform(Ntr[pcols].values.astype(np.float32)))]).tocsr()
y_ptrain = ptrain["label"].astype(int).values
pmodel = LogisticRegression(C=1.0, class_weight="balanced", solver="lbfgs", max_iter=2000,
                            tol=1e-4, random_state=42)
pmodel.fit(Ptr, y_ptrain)
print(f"  model trained in {time.time()-t0:.1f}s")

# Full-URL platform-masked model scores.
full = joblib.load(os.path.join(CAND, "PLATFORM_MASK.joblib"))
tranco = load_tranco_rank(ROOT)
print("Scoring DEV/EXT_DEV with both branches...")
t0 = time.time()
branch = {}
for name, df in [("dev", DEV), ("ext_dev", EXT_DEV)]:
    urls = df["url"].astype(str).tolist()
    Xc = full["vectorizer"].transform(urls)
    N = platform_frame(urls, tranco, with_flags=False)
    Ns = full["scaler"].transform(N[full["numeric_feature_names"]].values.astype(np.float32))
    X = hstack([Xc, csr_matrix(Ns)]).tocsr()
    s_full = full["model"].predict_proba(X)[:, 1]
    s_plat = np.full(len(df), np.nan)
    mask = (df["platform"].values != "")
    if mask.any():
        Pc = pvec.transform(df.loc[mask, "path"].tolist())
        Pn = platform_numeric(df.loc[mask, "url"].tolist())
        PX = hstack([Pc, csr_matrix(pscaler.transform(Pn[pcols].values.astype(np.float32)))]).tocsr()
        s_plat[mask] = pmodel.predict_proba(PX)[:, 1]
    # Replace full score by platform score on platform rows.
    s_comb = s_full.copy()
    s_comb[mask] = s_plat[mask]
    branch[name] = {"y": df["label"].astype(int).values, "mask": mask,
                    "full": s_full, "platform": s_plat, "combined": s_comb,
                    "df": df}
    print(f"  {name} done {time.time()-t0:.1f}s  platform rows={int(mask.sum())}")

results = {}
for name in ("dev", "ext_dev"):
    b = branch[name]
    y = b["y"]
    mask = b["mask"]
    plat = evaluate(y[mask], b["platform"][mask]) if mask.any() else {}
    full_plat = evaluate(y[mask], b["full"][mask]) if mask.any() else {}
    comb = evaluate(y, b["combined"])
    full_all = evaluate(y, b["full"])
    results[name] = {
        "platform_subset": plat,
        "full_model_on_platform_subset": full_plat,
        "combined_all": comb,
        "full_model_all": full_all,
        "platform_auc": float(roc_auc_score(y[mask], b["platform"][mask])) if mask.any() and len(set(y[mask])) > 1 else None,
        "full_auc_platform_subset": float(roc_auc_score(y[mask], b["full"][mask])) if mask.any() and len(set(y[mask])) > 1 else None,
        "n_platform": int(mask.sum()),
        "n_platform_phish": int(((y == 1) & mask).sum()),
        "n_platform_legit": int(((y == 0) & mask).sum()),
    }
    c = comb["at_fpr_le_0.01"]
    f = full_all["at_fpr_le_0.01"]
    print(f"\n{name}: combined @1% rec={c['recall']:.4f} fpr={c['fpr']:.4f} thr={c['threshold']:.4f} "
          f"(full rec={f['recall']:.4f})")
    print(f"  platform subset: AUC={results[name]['platform_auc']} "
          f"full_auc={results[name]['full_auc_platform_subset']}")
    if mask.any():
        p = plat.get("at_fpr_le_0.01") or plat.get("at_0.5", {})
        print(f"  platform @1% rec={p.get('recall')} fpr={p.get('fpr')}")

# Threshold sweep on combined scores, using DEV only.
b = branch["dev"]
y = b["y"]
print("\nDEV threshold sweep (combined):")
rows = []
for t in np.arange(0.30, 0.991, 0.01):
    pred = b["combined"] >= t
    rec = float(pred[y == 1].mean())
    fpr = float(pred[y == 0].mean())
    rows.append((float(t), rec, fpr))
rows.sort(key=lambda r: (abs(r[2] - 0.01), -r[1]))
print("closest to 1% FPR:", rows[0])

# Save artifact and experiment.
art_path = os.path.join(CAND, "PLATFORM_SPECIALIST.joblib")
joblib.dump({"model": pmodel, "vectorizer": pvec, "scaler": pscaler,
             "numeric_feature_names": pcols, "kind": "platform_path_specialist"},
            art_path)
eid = next_exp_id()
with open(os.path.join(EXP, f"{eid}.json"), "w", encoding="utf-8") as f:
    json.dump({"experiment_id": eid, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "dataset_version": "v2_platform_specialist", "train_split": "TRAIN+EXT_TRAIN platform rows",
               "dev_split": "DEV", "model_name": "PLATFORM_SPECIALIST",
               "representation": "path char_tfidf_2_5 + platform/lexical numeric",
               "hyperparameters": {"C": 1.0, "class_weight": "balanced"},
               "random_seed": 42, "results": results,
               "model_artifact_path": art_path},
              f, indent=2, default=str)
results["experiment_id"] = eid
with open(os.path.join(OUT, "platform_specialist.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, default=str)
print("\nSaved", os.path.join(OUT, "platform_specialist.json"), "and", eid)
