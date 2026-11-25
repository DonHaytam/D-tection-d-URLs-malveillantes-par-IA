"""Integrate URL dataset (450K) into training."""
import sys, os, json, csv
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

# Load URL dataset
url_rows = []
with open(os.path.join(ROOT, "data/Phishing URL dataset/Phishing URL dataset/URL dataset.csv"), 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        url_rows.append(r)

print(f"URL dataset: {len(url_rows)} rows")

# Domain overlap check
dev_domains = set(DEV["registrable_domain"].dropna().astype(str))
train_domains = set(TRAIN["registrable_domain"].dropna().astype(str))

def get_rd(url):
    host = url.split('://')[-1].split('/')[0].split(':')[0].lower() if '://' in url else url.split('/')[0].split(':')[0].lower()
    parts = host.split('.')
    return '.'.join(parts[-2:]) if len(parts) >= 2 else host

# Filter: remove domains that overlap with DEV or TRAIN
new_legit = []
new_phish = []
for r in url_rows:
    rd = get_rd(r['url'])
    if rd in dev_domains:
        continue  # domain overlap with DEV — skip
    if r['type'] == 'legitimate':
        new_legit.append(r)
    elif r['type'] == 'phishing':
        new_phish.append(r)

print(f"After domain-disjoint filter: legit={len(new_legit)}, phish={len(new_phish)}")

# Sample to keep manageable
np.random.seed(42)
legit_sample = pd.DataFrame(new_legit).sample(n=min(20000, len(new_legit)), random_state=42)
phish_sample = pd.DataFrame(new_phish).sample(n=min(20000, len(new_phish)), random_state=42)
print(f"Sampled: legit={len(legit_sample)}, phish={len(phish_sample)}")

# Build aligned DataFrame
def align(df, label):
    out = pd.DataFrame()
    out['url'] = df['url']
    out['label'] = 1 if label == 'legitimate' else 0
    out['source'] = 'url_dataset_450k'
    out['collection_date'] = 'unknown'
    out['domain'] = df['url'].map(lambda u: u.split('://')[-1].split('/')[0].split(':')[0].lower() if '://' in u else u.split('/')[0].split(':')[0].lower())
    out['registrable_domain'] = out['domain'].map(lambda h: '.'.join(h.split('.')[-2:]) if '.' in h else h)
    out['tld'] = out['domain'].map(lambda h: h.split('.')[-1] if '.' in h else '')
    out['scheme'] = out['url'].map(lambda u: u.split('://')[0].lower() if '://' in u else 'https')
    out['path'] = out['url'].map(lambda u: u.split('://',1)[-1].split('/',1)[1].split('?')[0] if '://' in u and '/' in u.split('://',1)[-1] else '')
    out['query'] = out['url'].map(lambda u: u.split('?',1)[1] if '?' in u else '')
    out['fragment'] = ''
    out['dataset_version'] = 'v2'
    return out

legit_aligned = align(legit_sample, 'legitimate')
phish_aligned = align(phish_sample, 'phishing')
new_data = pd.concat([legit_aligned, phish_aligned], ignore_index=True)
print(f"New data: {len(new_data)} ({new_data['label'].value_counts().to_dict()})")

# Combine with existing TRAIN
augmented = pd.concat([TRAIN, new_data[TRAIN.columns]], ignore_index=True)
print(f"Augmented TRAIN: {len(augmented)} (was {len(TRAIN)})")

# Train
Xtr = augmented["url"].astype(str).tolist()
ytr = augmented["label"].astype(int).values
Xdev = DEV["url"].astype(str).tolist()
ydev = DEV["label"].astype(int).values

# Reuse existing vectorizer
m1_art = joblib.load(os.path.join(ROOT, "models/versions/M1_LR.joblib"))
vec = m1_art["vectorizer"]
Xtr_c = vec.transform(Xtr)
Xdev_c = vec.transform(Xdev)
print(f"Feature shape: {Xtr_c.shape}")

t0 = __import__('time').time()
m = LogisticRegression(C=1.0, class_weight="balanced", solver="saga", max_iter=3000, random_state=42, n_jobs=-1)
m.fit(Xtr_c, ytr)
tr = __import__('time').time() - t0
sc = m.predict_proba(Xdev_c)[:, 1]
met = compute_metrics(ydev, sc)
met["ece"] = expected_calibration_error(ydev, sc)
print(f"\n  acc={met['accuracy']:.4f} rec={met['recall']:.4f} fpr={met['fpr']:.4f} f1={met['f1']:.4f} auc={met['roc_auc']:.4f} ece={met['ece']:.4f} train={tr:.1f}s")

# Diagnostic URLs
diag_urls = [
    "https://www.paypal.com/signin",
    "https://www.dropbox.com/login",
    "https://github.com/login",
    "https://accounts.google.com/signin",
    "https://login.microsoftonline.com/",
    "https://www.amazon.com/ap/signin",
    "https://www.apple.com/shop/account/home",
    "https://www.linkedin.com/login",
]
diag_scores = m.predict_proba(vec.transform(diag_urls))[:, 1]
print("\n=== DIAGNOSTIC URLS ===")
for u, s in zip(diag_urls, diag_scores):
    print(f"  {s*100:6.2f}%  {u}")

# Save
import json as _j
eid = f"EXP{len(os.listdir(os.path.join(ROOT, 'experiments/results')))+1:03d}"
joblib.dump({"model": m, "vectorizer": vec}, os.path.join(ROOT, "models/versions", "URLDATA_LR.joblib"))
exp = {"experiment_id": eid, "timestamp": __import__('time').strftime("%Y-%m-%dT%H:%M:%S"),
       "dataset_version": "v2", "train_split": "TRAIN+URLdataset40K", "dev_split": "DEV",
       "n_train": len(ytr), "n_dev": len(ydev), "model_name": "URLDATA_LR",
       "representation": "char_tfidf_3_5 + 40k URL dataset (domain-disjoint)",
       "hyperparameters": {"C": 1.0, "class_weight": "balanced"}, "random_seed": 42,
       "metrics_dev": met, "training_time_s": round(tr, 3),
       "model_artifact_path": os.path.join(ROOT, "models/versions", "URLDATA_LR.joblib")}
with open(os.path.join(ROOT, "experiments/results", eid + ".json"), "w") as f:
    _j.dump(exp, f, indent=2, default=str)
print(f"\nSaved {eid}")
