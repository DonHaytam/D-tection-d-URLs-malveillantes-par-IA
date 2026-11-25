"""Diagnose external URL dataset label quality and model behaviour."""
import sys, os, csv, re, json
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

import numpy as np
import pandas as pd
import joblib
from collections import Counter, defaultdict

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
DEV = pd.read_csv(os.path.join(ROOT, "data/splits/DEV.csv"))
TRAIN = pd.read_csv(os.path.join(ROOT, "data/splits/TRAIN.csv"))

# Load models
base = joblib.load(os.path.join(ROOT, "models/versions/M1_LR_HARDNEG.joblib"))
exp27 = joblib.load(os.path.join(ROOT, "models/versions/URLDATA_LR.joblib"))

def score(art, urls):
    return art["model"].predict_proba(art["vectorizer"].transform(urls))[:, 1]

# Score DEV
dev_urls = DEV["url"].astype(str).tolist()
dev_y = DEV["label"].astype(int).values
for name, art in [("M1_LR_HARDNEG", base), ("URLDATA_LR", exp27)]:
    sc = score(art, dev_urls)
    fp = (dev_y == 0) & (sc >= 0.5)
    tp = (dev_y == 1) & (sc >= 0.5)
    print(f"\n=== {name} ===")
    print(f"FPR@0.5={fp.sum()/max((dev_y==0).sum(),1):.4f} recall@0.5={tp.sum()/max((dev_y==1).sum(),1):.4f}")
    print("Top false positives:")
    idx = np.where(fp)[0]
    idx = idx[np.argsort(-sc[idx])][:10]
    for i in idx:
        print(f"  {sc[i]*100:6.2f}%  {dev_urls[i][:120]}")

# Load external URL dataset
ext_path = os.path.join(ROOT, "data/Phishing URL dataset/Phishing URL dataset/URL dataset.csv")
ext = []
with open(ext_path, "r", encoding="utf-8", errors="replace") as f:
    r = csv.DictReader(f)
    for row in r:
        ext.append((row["url"], row["type"]))
print(f"\nExternal URL dataset: {len(ext)}")

# Score a sample of external data with baseline
rng = np.random.default_rng(42)
for label in ["legitimate", "phishing"]:
    subset = [u for u, t in ext if t == label]
    samp = [subset[i] for i in rng.choice(len(subset), size=min(5000, len(subset)), replace=False)]
    sc = score(base, samp)
    print(f"\nExternal {label}: n={len(subset)}, sample={len(samp)}")
    print(f"  score>=0.5: {(sc>=0.5).sum()} ({(sc>=0.5).mean()*100:.1f}%)")
    print(f"  mean={sc.mean():.4f} median={np.median(sc):.4f} p90={np.percentile(sc,90):.4f}")
    # show suspicious cases
    if label == "legitimate":
        idx = np.where(sc >= 0.5)[0]
        print("  Legit scored as phishing (possible hard negatives or label noise):")
    else:
        idx = np.where(sc < 0.5)[0]
        print("  Phish scored as legit (possible label noise):")
    idx = idx[np.argsort(-sc[idx])][:8] if label == "legitimate" else idx[np.argsort(sc[idx])][:8]
    for i in idx:
        print(f"    {sc[i]*100:6.2f}%  {samp[i][:120]}")

# Check label conflicts: exact URL in both labels
url_labels = defaultdict(set)
for u, t in ext:
    url_labels[u.strip()].add(t)
conflicts = {u: v for u, v in url_labels.items() if len(v) > 1}
print(f"\nExact URL label conflicts: {len(conflicts)}")
for u, v in list(conflicts.items())[:5]:
    print(" ", u, v)

# Normalized duplicates within external
def norm(u):
    u = u.strip().lower()
    u = re.sub(r"^https?://", "", u)
    u = u.split("#")[0]
    if u.startswith("www."):
        u = u[4:]
    return u.rstrip("/")
norm_map = defaultdict(list)
for u, t in ext:
    norm_map[norm(u)].append((u, t))
dups = {k: v for k, v in norm_map.items() if len(v) > 1}
print(f"Normalized duplicate groups: {len(dups)}")
conflict_norm = {k: set(t for _, t in v) for k, v in dups.items() if len(set(t for _, t in v)) > 1}
print(f"Normalized label conflicts: {len(conflict_norm)}")

# Auth path detection
AUTH = re.compile(r"(?:^|/)(login|signin|sign-in|sign_in|auth|account|accounts|verify|verification|password|oauth|register|signup|sign-up|security|checkout|payment|billing|wp-login\.php|login\.php|signin\.php)(?:/|$|[.?])", re.I)
def is_auth(u):
    try:
        p = u.split("://", 1)[1]
        path = p.split("/", 1)[1] if "/" in p else ""
        return bool(AUTH.search("/" + path.split("?")[0]))
    except Exception:
        return False

for label in ["legitimate", "phishing"]:
    subset = [u for u, t in ext if t == label and is_auth(u)]
    print(f"External {label} auth-path URLs: {len(subset)}")
    for u in subset[:5]:
        print("  ", u[:120])

# Compare with Phishing URLs.csv (all phishing)
ph_path = os.path.join(ROOT, "data/Phishing URL dataset/Phishing URL dataset/Phishing URLs.csv")
ph_urls = []
with open(ph_path, "r", encoding="utf-8", errors="replace") as f:
    r = csv.DictReader(f)
    for row in r:
        ph_urls.append(row["url"])
print(f"\nPhishing URLs.csv: {len(ph_urls)}")
ext_ph = set(u for u, t in ext if t == "phishing")
print(f"Overlap with external phishing: {len(set(ph_urls) & ext_ph)}")
print(f"Phishing URLs.csv not in external: {len(set(ph_urls) - ext_ph)}")
