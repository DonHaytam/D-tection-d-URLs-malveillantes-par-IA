"""HTTP vs HTTPS ablation."""
import sys, os, json
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
Xtr = TRAIN["url"].astype(str).tolist()
ytr = TRAIN["label"].astype(int).values
Xdev = DEV["url"].astype(str).tolist()
ydev = DEV["label"].astype(int).values

# A: with scheme (full URL) - baseline
vec_a = TfidfVectorizer(analyzer="char", ngram_range=(3,5), min_df=3, max_features=20000, lowercase=True, sublinear_tf=True)
Xtr_a = vec_a.fit_transform(Xtr)
Xdev_a = vec_a.transform(Xdev)
m_a = LogisticRegression(C=1.0, class_weight="balanced", solver="saga", max_iter=2000, random_state=42, n_jobs=-1)
m_a.fit(Xtr_a, ytr)
sc_a = m_a.predict_proba(Xdev_a)[:, 1]
met_a = compute_metrics(ydev, sc_a); met_a["ece"] = expected_calibration_error(ydev, sc_a)
print(f"With scheme:    acc={met_a['accuracy']:.4f} rec={met_a['recall']:.4f} fpr={met_a['fpr']:.4f} auc={met_a['roc_auc']:.4f}")

# B: without scheme
def strip_scheme(urls):
    return [u.split("://",1)[-1] if "://" in u else u for u in urls]
Xtr_b = strip_scheme(Xtr); Xdev_b = strip_scheme(Xdev)
vec_b = TfidfVectorizer(analyzer="char", ngram_range=(3,5), min_df=3, max_features=20000, lowercase=True, sublinear_tf=True)
Xtr_bv = vec_b.fit_transform(Xtr_b)
Xdev_bv = vec_b.transform(Xdev_b)
m_b = LogisticRegression(C=1.0, class_weight="balanced", solver="saga", max_iter=2000, random_state=42, n_jobs=-1)
m_b.fit(Xtr_bv, ytr)
sc_b = m_b.predict_proba(Xdev_bv)[:, 1]
met_b = compute_metrics(ydev, sc_b); met_b["ece"] = expected_calibration_error(ydev, sc_b)
print(f"Without scheme: acc={met_b['accuracy']:.4f} rec={met_b['recall']:.4f} fpr={met_b['fpr']:.4f} auc={met_b['roc_auc']:.4f}")

# C: scheme replaced with placeholder (remove http/https distinction)
def replace_scheme(urls):
    return ["SCHEME" + u.split("://",1)[-1] if "://" in u else u for u in urls]
Xtr_c = replace_scheme(Xtr); Xdev_c = replace_scheme(Xdev)
vec_c = TfidfVectorizer(analyzer="char", ngram_range=(3,5), min_df=3, max_features=20000, lowercase=True, sublinear_tf=True)
Xtr_cv = vec_c.fit_transform(Xtr_c)
Xdev_cv = vec_c.transform(Xdev_c)
m_c = LogisticRegression(C=1.0, class_weight="balanced", solver="saga", max_iter=2000, random_state=42, n_jobs=-1)
m_c.fit(Xtr_cv, ytr)
sc_c = m_c.predict_proba(Xdev_cv)[:, 1]
met_c = compute_metrics(ydev, sc_c); met_c["ece"] = expected_calibration_error(ydev, sc_c)
print(f"Scheme masked:  acc={met_c['accuracy']:.4f} rec={met_c['recall']:.4f} fpr={met_c['fpr']:.4f} auc={met_c['roc_auc']:.4f}")

# HTTP-specific analysis
http_urls = [u for u in Xdev if u.startswith("http://")]
https_urls = [u for u in Xdev if u.startswith("https://")]
print(f"\nHTTP URLs in DEV: {len(http_urls)}, HTTPS: {len(https_urls)}")
print(f"HTTP phishing rate: {sum(1 for u in http_urls if DEV[DEV['url']==u]['label'].values[0]==1)/len(http_urls):.4f}" if http_urls else "N/A")
# FP rate for HTTP legitimate
legit_http = [u for u in Xdev if u.startswith("http://") and DEV[DEV['url']==u]['label'].values[0]==0]
print(f"Legitimate HTTP URLs: {len(legit_http)}")
if legit_http:
    idx = [Xdev.index(u) for u in legit_http]
    http_fp = sum(1 for i in idx if (scores[i] if 'scores' in dir() else sc_a[i]) >= 0.5)
    print(f"HTTP legitimate flagged as phishing: {http_fp}/{len(legit_http)} = {http_fp/len(legit_http):.4f}")

import json as _j
result = {
    "with_scheme": {"accuracy": met_a["accuracy"], "recall": met_a["recall"], "fpr": met_a["fpr"], "roc_auc": met_a["roc_auc"], "ece": met_a["ece"]},
    "without_scheme": {"accuracy": met_b["accuracy"], "recall": met_b["recall"], "fpr": met_b["fpr"], "roc_auc": met_b["roc_auc"], "ece": met_b["ece"]},
    "scheme_masked": {"accuracy": met_c["accuracy"], "recall": met_c["recall"], "fpr": met_c["fpr"], "roc_auc": met_c["roc_auc"], "ece": met_c["ece"]},
    "n_http": len(http_urls), "n_https": len(https_urls), "n_legit_http": len(legit_http),
}
with open(os.path.join(ROOT, "reports/tables/http_https_ablation.json"), "w") as f:
    _j.dump(result, f, indent=2)
print("\nSaved http_https_ablation.json")
