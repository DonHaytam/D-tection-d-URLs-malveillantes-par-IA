"""Platform-aware reputation experiment.

Motivation: binary Tranco reputation features push URLs hosted on free hosts,
shorteners and document platforms toward "legitimate" even when the page path
is clearly phishing.  For such shared platforms the reputation of the
registrable domain says little about the individual page, so we mask Tranco
features and expose explicit platform interactions instead.
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
from sklearn.metrics import roc_curve

from src.evaluation.metrics import compute_metrics, expected_calibration_error
from src.data.provenance import registrable_domain
from src.data.validation import extract_components
from hybrid_features import load_tranco_rank, numeric_frame

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
OUT = os.path.join(ROOT, "reports", "data_expansion_public")
CAND = os.path.join(ROOT, "models", "versions", "candidates")
EXP = os.path.join(ROOT, "experiments", "results")

SHORTENERS = {
    "bit.ly", "t.co", "goo.gl", "tinyurl.com", "is.gd", "buff.ly", "ow.ly", "rb.gy",
    "cutt.ly", "shorturl.at", "rebrand.ly", "tiny.cc", "lnkd.in", "t.ly", "s.id",
    "v.gd", "qr.ae", "adf.ly", "sh.st", "clck.ru", "shorturl.com", "tiny.one",
    "urlz.fr", "x.co", "me2.do", "j.mp", "bit.do", "soo.gd", "trib.al", "dlvr.it",
    "ift.tt", "wp.me", "flip.it", "po.st", "snip.ly", "surl.li", "shorte.st",
    "tr.ee", "urlgeni.us", "tinyurl.io", "rebrandly.com", "short.io", "bl.ink",
}
FREE_HOSTS = {
    "3utilities.com", "ocry.com", "mefound.com", "000webhostapp.com", "weebly.com",
    "wixsite.com", "blogspot.com", "wordpress.com", "github.io", "gitlab.io",
    "netlify.app", "vercel.app", "herokuapp.com", "glitch.me", "repl.co",
    "firebaseapp.com", "web.app", "pages.dev", "workers.dev", "rf.gd", "42web.io",
    "infinityfree.net", "epizy.com", "byethost.com", "freehostia.com", "awardspace.com",
    "000space.com", "x10.bz", "in.net", "pe.hu", "esy.es", "hol.es", "16mb.com",
    "my.id", "web.id", "site88.net", "freewebhostingarea.com", "atw.hu", "thats.im",
    "youdontcare.com", "babinet.cz", "home.pl", "pp.ua", "pp.ru",
}
DOC_HOSTS = {
    "docs.google.com", "drive.google.com", "forms.gle", "script.google.com",
    "sites.google.com", "forms.office.com", "outlook.office.com", "onedrive.live.com",
    "sharepoint.com", "notion.so", "notion.site", "airtable.com", "typeform.com",
    "jotform.com", "cognitoforms.com", "paperform.co", "forms.app", "surveyheart.com",
    "sendgrid.net", "mailchimp.com", "list-manage.com",
}
CLOUD_HOSTS = {
    "amazonaws.com", "cloudfront.net", "azurewebsites.net", "appspot.com",
    "googleusercontent.com", "blogspot.com", "windows.net", "digitaloceanspaces.com",
    "storage.googleapis.com", "r2.dev", "backblazeb2.com", "linodeobjects.com",
}


def platform_of(url):
    try:
        host = extract_components(url)["host"].lower()
    except Exception:
        return "", ""
    rd = registrable_domain(host)
    if any(host == d or host.endswith("." + d) for d in DOC_HOSTS):
        return "doc", rd
    if rd in SHORTENERS:
        return "shortener", rd
    if any(rd == d or rd.endswith("." + d) for d in FREE_HOSTS):
        return "free", rd
    if any(rd == d or rd.endswith("." + d) for d in CLOUD_HOSTS):
        return "cloud", rd
    return "", rd


TR_STRICT = re.compile(
    r"(?:^|/)(login|signin|sign-in|sign_in|logon|auth|account|accounts|verify|verification|"
    r"password|passwd|oauth|register|signup|sign-up|security|checkout|payment|billing|"
    r"wp-login\.php|login\.php|signin\.php)(?:/|$|[.?])", re.I)


def platform_frame(urls, tranco_rank, with_flags=True):
    base = numeric_frame(urls, tranco_rank)
    platforms, rds = [], []
    for u in urls:
        p, rd = platform_of(u)
        platforms.append(p)
        rds.append(rd)
    platform = np.array([1.0 if p else 0.0 for p in platforms])
    is_doc = np.array([1.0 if p == "doc" else 0.0 for p in platforms])
    is_short = np.array([1.0 if p == "shortener" else 0.0 for p in platforms])
    is_free = np.array([1.0 if p == "free" else 0.0 for p in platforms])
    is_cloud = np.array([1.0 if p == "cloud" else 0.0 for p in platforms])
    auth = base["auth_path_flag"].values
    tok = base["auth_token_count"].values
    query = base["has_query"].values
    path_depth = base["path_depth"].values
    # Mask reputation for shared platforms.
    keep = 1.0 - platform
    for col in ("tranco_present", "tranco_top10k", "tranco_top100k", "tranco_top1m"):
        base[col] = base[col].values * keep
    ranks = np.array([tranco_rank.get(d, 0) for d in rds], dtype=float) * keep
    base["tranco_log_rank"] = np.where(ranks > 0, np.log1p(ranks), 0.0)
    present = base["tranco_present"].values
    top10k = base["tranco_top10k"].values
    base["auth_x_top10k"] = auth * top10k
    base["auth_x_present"] = auth * present
    base["auth_x_absent"] = auth * (1.0 - present)
    base["token_x_present"] = tok * present
    base["token_x_absent"] = tok * (1.0 - present)
    if with_flags:
        extra = pd.DataFrame({
            "platform_flag": platform,
            "platform_doc": is_doc,
            "platform_shortener": is_short,
            "platform_free": is_free,
            "platform_cloud": is_cloud,
            "platform_x_auth": platform * auth,
            "platform_x_token": platform * tok,
            "platform_x_query": platform * query,
            "platform_x_pathdepth": platform * path_depth,
            "free_x_auth": is_free * auth,
            "short_x_query": is_short * query,
            "doc_x_auth": is_doc * auth,
        })
        base = pd.concat([base.reset_index(drop=True), extra.reset_index(drop=True)], axis=1)
    return base


def next_exp_id():
    nums = []
    for f in os.listdir(EXP):
        if f.startswith("EXP") and f.endswith(".json"):
            try:
                nums.append(int(f[3:6]))
            except ValueError:
                pass
    return f"EXP{max(nums, default=0) + 1:03d}"


def evaluate(y, s):
    m = compute_metrics(y, s, threshold=0.5)
    m["ece"] = expected_calibration_error(y, s)
    fpr, tpr, thr = roc_curve(y, s)
    out = {"at_0.5": m}
    for target in [0.005, 0.01, 0.02, 0.0381, 0.05]:
        ok = fpr <= target
        if ok.any():
            t = float(thr[ok][int(np.argmax(tpr[ok]))])
            out[f"at_fpr_le_{target}"] = {"threshold": t, **compute_metrics(y, s, threshold=t)}
    pred3 = np.where(s >= 0.75, 1, np.where(s < 0.25, 0, 2))
    legit = y == 0
    phish = y == 1
    out["three_class_0.25_0.75"] = {
        "strict_recall": float((pred3[phish] == 1).mean()),
        "detected_incl_review": float((pred3[phish] >= 1).mean()),
        "fpr": float((pred3[legit] == 1).mean()),
        "review_rate": float((pred3 == 2).mean()),
    }
    return out


def group_metrics(df, s, strict_recall_thr):
    y = df["label"].astype(int).values
    m = df["platform"].values if "platform" in df else np.array([""] * len(df))
    out = {}
    for grp in sorted(set(m)):
        sel = m == grp
        if sel.sum() == 0:
            continue
        out[str(grp)] = {
            "n": int(sel.sum()),
            "legit": int(((y == 0) & sel).sum()),
            "phish": int(((y == 1) & sel).sum()),
            "mean_score": float(s[sel].mean()),
            "phish_recall_at_1pct": float((s[sel & (y == 1)] >= strict_recall_thr).mean()) if ((sel & (y == 1)).sum() > 0) else None,
            "legit_fpr_at_1pct": float((s[sel & (y == 0)] >= strict_recall_thr).mean()) if ((sel & (y == 0)).sum() > 0) else None,
        }
    return out


TRAIN = pd.read_csv(os.path.join(ROOT, "data/splits/TRAIN.csv"), usecols=["url", "label"])
DEV = pd.read_csv(os.path.join(ROOT, "data/splits/DEV.csv"), usecols=["url", "label"])
EXT_TRAIN = pd.read_csv(os.path.join(ROOT, "data/integrated/external_train.csv"), usecols=["url", "label"])
EXT_DEV = pd.read_csv(os.path.join(ROOT, "data/integrated/external_dev.csv"), usecols=["url", "label"])
for df in (DEV, EXT_DEV):
    df["platform"] = df["url"].map(lambda u: platform_of(u)[0] or "other")

ext_sample = pd.concat([
    EXT_TRAIN[EXT_TRAIN.label == 0].sample(n=20000, random_state=42),
    EXT_TRAIN[EXT_TRAIN.label == 1].sample(n=20000, random_state=42),
], ignore_index=True)
train = pd.concat([TRAIN, ext_sample], ignore_index=True).sample(frac=1.0, random_state=42).reset_index(drop=True)
train_urls = train["url"].astype(str).tolist()
dev_urls = DEV["url"].astype(str).tolist()
ext_urls = EXT_DEV["url"].astype(str).tolist()
y_train = train["label"].astype(int).values
y_dev = DEV["label"].astype(int).values
y_ext = EXT_DEV["label"].astype(int).values
print(f"train={len(train)} dev={len(DEV)} ext_dev={len(EXT_DEV)}")
print("DEV platform groups:", DEV["platform"].value_counts().to_dict())
print("EXT platform groups:", EXT_DEV["platform"].value_counts().to_dict())

tranco = load_tranco_rank(ROOT)
print("Building char TF-IDF...")
t0 = time.time()
vec = TfidfVectorizer(analyzer="char", ngram_range=(3, 5), min_df=3, max_features=20000,
                      lowercase=True, sublinear_tf=True)
Xtr_char = vec.fit_transform(train_urls)
Xdev_char = vec.transform(dev_urls)
Xext_char = vec.transform(ext_urls)
print(f"  char {time.time()-t0:.1f}s shape={Xtr_char.shape}")

CONFIGS = [("PLATFORM_MASK", False), ("PLATFORM_FLAGS", True)]
results = {}
for name, with_flags in CONFIGS:
    print(f"\n=== {name} (flags={with_flags}) ===")
    t0 = time.time()
    Ntr = platform_frame(train_urls, tranco, with_flags=with_flags)
    Ndev = platform_frame(dev_urls, tranco, with_flags=with_flags)
    Next = platform_frame(ext_urls, tranco, with_flags=with_flags)
    cols = list(Ntr.columns)
    scaler = StandardScaler()
    Ntr_s = scaler.fit_transform(Ntr[cols].values.astype(np.float32))
    Ndev_s = scaler.transform(Ndev[cols].values.astype(np.float32))
    Next_s = scaler.transform(Next[cols].values.astype(np.float32))
    Xtr = hstack([Xtr_char, csr_matrix(Ntr_s)]).tocsr()
    Xdev = hstack([Xdev_char, csr_matrix(Ndev_s)]).tocsr()
    Xext = hstack([Xext_char, csr_matrix(Next_s)]).tocsr()
    print(f"  features {Xtr.shape} built in {time.time()-t0:.1f}s")
    model = LogisticRegression(C=1.0, class_weight="balanced", solver="lbfgs", max_iter=300,
                               tol=1e-3, random_state=42, n_jobs=-1)
    t0 = time.time()
    model.fit(Xtr, y_train)
    tr_time = time.time() - t0
    s_dev = model.predict_proba(Xdev)[:, 1]
    s_ext = model.predict_proba(Xext)[:, 1]
    res_dev = evaluate(y_dev, s_dev)
    res_ext = evaluate(y_ext, s_ext)
    a = res_dev["at_0.5"]
    b = res_dev["at_fpr_le_0.01"]
    t3 = res_dev["three_class_0.25_0.75"]
    ae = res_ext["at_0.5"]
    be = res_ext["at_fpr_le_0.01"]
    print(f"  DEV @0.5 rec={a['recall']:.4f} fpr={a['fpr']:.4f} auc={a['roc_auc']:.4f}")
    print(f"  DEV @1% rec={b['recall']:.4f} fpr={b['fpr']:.4f} thr={b['threshold']:.4f}")
    print(f"  DEV 3c rec={t3['strict_recall']:.4f} fpr={t3['fpr']:.4f}")
    print(f"  EXT @0.5 rec={ae['recall']:.4f} fpr={ae['fpr']:.4f} auc={ae['roc_auc']:.4f}")
    print(f"  EXT @1% rec={be['recall']:.4f} fpr={be['fpr']:.4f}")
    res_dev["platform_groups"] = group_metrics(DEV, s_dev, b["threshold"])
    res_ext["platform_groups"] = group_metrics(EXT_DEV, s_ext, be["threshold"])
    results[name] = {"dev": res_dev, "external_dev": res_ext,
                     "config": {"with_flags": with_flags, "n_features": int(Xtr.shape[1]),
                                "n_train": int(len(train))},
                     "training_time_s": round(tr_time, 2)}
    art_path = os.path.join(CAND, f"{name}.joblib")
    joblib.dump({"model": model, "vectorizer": vec, "scaler": scaler,
                 "numeric_feature_names": cols, "kind": "hybrid_platform"}, art_path)
    eid = next_exp_id()
    with open(os.path.join(EXP, f"{eid}.json"), "w", encoding="utf-8") as f:
        json.dump({"experiment_id": eid, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                   "dataset_version": "v2_platform_aware", "train_split": "TRAIN+EXT40K",
                   "dev_split": "DEV", "model_name": name,
                   "representation": "char_tfidf_3_5 + platform-masked numeric/reputation",
                   "hyperparameters": {"C": 1.0, "class_weight": "balanced", "with_flags": with_flags},
                   "random_seed": 42, "metrics_dev": a, "metrics_dev_fpr_le_0.01": b,
                   "metrics_dev_three_class": t3, "metrics_external_dev": ae,
                   "training_time_s": round(tr_time, 2), "model_artifact_path": art_path},
                  f, indent=2, default=str)
    results[name]["experiment_id"] = eid
    print(f"  saved {eid}")
    del model, Xtr, Xdev, Xext
    gc.collect()

with open(os.path.join(OUT, "platform_aware.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, default=str)
print("\nSaved", os.path.join(OUT, "platform_aware.json"))
