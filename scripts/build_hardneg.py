"""Phase 4-5 — Build hard-negative legitimate authentication dataset from Tranco."""
import sys, os, json, zipfile
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

import pandas as pd
import numpy as np

ROOT = "D:/openhands/projects/v2/phishing_ai_master"

# Load Tranco
with zipfile.ZipFile(os.path.join(ROOT, "data/raw/tranco_top1m.csv.zip")) as z:
    with z.open("top-1m.csv") as f:
        tranco = pd.read_csv(f, header=None, names=["rank", "domain"])

# Authentication paths
auth_paths = [
    "/login", "/signin", "/sign-in", "/auth", "/auth/login", "/account",
    "/accounts", "/account/security", "/account/settings", "/password",
    "/password/reset", "/forgot-password", "/verify", "/security",
    "/checkout", "/payment", "/billing", "/oauth", "/oauth/authorize",
    "/account/login", "/user/login", "/members/login", "/admin/login",
    "/wp-login.php", "/login.php", "/signin.php",
]

# Build legitimate auth URLs from Tranco top domains
# Use top 50k domains to ensure legitimacy
domains = tranco["domain"].head(50000).astype(str).tolist()
rows = []
for d in domains:
    for path in auth_paths:
        rows.append({
            "url": f"https://{d}{path}",
            "label": 0,
            "source": "tranco_auth_hardneg",
            "collection_date": "2026-11-25 (constructed from Tranco)",
        })

hn_df = pd.DataFrame(rows)
print(f"Hard-negative auth URLs: {len(hn_df)}")
print(f"Unique domains: {hn_df['url'].map(lambda u: u.split('://')[1].split('/')[0]).nunique()}")

# Save
os.makedirs(os.path.join(ROOT, "data/interim"), exist_ok=True)
hn_df.to_csv(os.path.join(ROOT, "data/interim/hn_legit_auth.csv"), index=False)
print("Saved hn_legit_auth.csv")

# Also build hard-positive phishing without obvious keywords
# From existing phishing data, select those without common auth keywords
import pandas as pd
TRAIN = pd.read_csv(os.path.join(ROOT, "data/splits/TRAIN.csv"))
phish = TRAIN[TRAIN["label"]==1].copy()
# Phishing without auth keywords
no_kw = ~phish["url"].str.lower().str.contains("login|signin|verify|secure|account|password|auth|paypal|amazon|bank", regex=True)
hard_pos = phish[no_kw].copy()
print(f"Hard-positive phishing (no obvious keywords): {len(hard_pos)}")
hard_pos.to_csv(os.path.join(ROOT, "data/interim/hard_pos_phishing.csv"), index=False)
print("Saved hard_pos_phishing.csv")
