"""Check Tranco coverage of DEV errors and auth URLs (passive, no network)."""
import os
import sys
import zipfile
import re

sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

import numpy as np
import pandas as pd
import joblib

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
AUTH_RE = re.compile(
    r"(?:^|/)(login|signin|sign-in|sign_in|auth|account|accounts|verify|verification|"
    r"password|oauth|register|signup|sign-up|security|checkout|payment|billing|"
    r"wp-login\.php|login\.php|signin\.php)(?:/|$|[.?])", re.I)

def is_auth(u):
    try:
        p = str(u).split("://", 1)[1]
        path = p.split("/", 1)[1] if "/" in p else ""
        return bool(AUTH_RE.search("/" + path.split("?")[0]))
    except Exception:
        return False

with zipfile.ZipFile(os.path.join(ROOT, "data/raw/tranco_top1m.csv.zip")) as z:
    with z.open("top-1m.csv") as f:
        tranco = pd.read_csv(f, header=None, names=["rank", "domain"])
rank = {str(d).lower(): int(r) for r, d in zip(tranco["rank"], tranco["domain"])}
print(f"Tranco domains: {len(rank)}")

DEV = pd.read_csv(os.path.join(ROOT, "data/splits/DEV.csv"))
art = joblib.load(os.path.join(ROOT, "models/versions/M1_LR_HARDNEG.joblib"))
s = art["model"].predict_proba(art["vectorizer"].transform(DEV["url"].astype(str).tolist()))[:, 1]
DEV = DEV.copy()
DEV["score"] = s
DEV["auth"] = DEV["url"].map(is_auth)
DEV["tranco_rank"] = DEV["registrable_domain"].astype(str).str.lower().map(rank)

for lab, name in [(0, "legit"), (1, "phish")]:
    sub = DEV[DEV["label"] == lab]
    print(f"\n{name}: n={len(sub)} tranco_coverage={(sub['tranco_rank'].notna()).mean():.4f} "
          f"top10k={(sub['tranco_rank'] <= 10000).mean():.4f} top100k={(sub['tranco_rank'] <= 100000).mean():.4f}")
    for auth in [False, True]:
        a = sub[sub["auth"] == auth]
        if len(a):
            print(f"  auth={auth}: n={len(a)} tranco_cov={(a['tranco_rank'].notna()).mean():.4f} "
                  f"top10k={(a['tranco_rank'] <= 10000).mean():.4f} mean_score={a['score'].mean():.4f}")

print("\nLegit auth URLs:")
for _, r in DEV[(DEV["label"] == 0) & DEV["auth"]].sort_values("score", ascending=False).iterrows():
    print(f"  score={r['score']*100:6.2f}% tranco={r['tranco_rank']} {r['url'][:110]}")

print("\nTop 20 legit false positives (score>=0.5):")
fp = DEV[(DEV["label"] == 0) & (DEV["score"] >= 0.5)].sort_values("score", ascending=False).head(20)
for _, r in fp.iterrows():
    print(f"  score={r['score']*100:6.2f}% tranco={r['tranco_rank']} auth={r['auth']} {r['url'][:110]}")
