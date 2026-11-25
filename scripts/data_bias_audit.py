"""Phase 1 — Data bias audit: analyze URL types in TRAIN."""
import sys, os, json
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

import numpy as np
import pandas as pd

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
TRAIN = pd.read_csv(os.path.join(ROOT, "data/splits/TRAIN.csv"))
DEV = pd.read_csv(os.path.join(ROOT, "data/splits/DEV.csv"))

def url_type(u):
    u = str(u).lower()
    path = ""
    if "://" in u:
        rest = u.split("://", 1)[1]
        if "/" in rest:
            path = rest.split("/", 1)[1].lower()
    elif "/" in u:
        path = u.split("/", 1)[1].lower()
    path = path.split("?")[0].split("#")[0]
    if path in ("", "/"):
        return "homepage"
    if any(k in path for k in ["login", "signin", "sign-in", "auth", "authentication"]):
        return "authentication"
    if any(k in path for k in ["account", "accounts"]):
        return "account"
    if any(k in path for k in ["password", "reset", "forgot"]):
        return "password_reset"
    if any(k in path for k in ["verify", "security"]):
        return "security_verify"
    if any(k in path for k in ["checkout", "cart", "payment", "billing", "order"]):
        return "ecommerce"
    if any(k in path for k in ["api", "oauth", "token"]):
        return "api_auth"
    if any(k in path for k in ["support", "help", "contact"]):
        return "support"
    if any(k in path for k in ["dashboard", "admin", "panel"]):
        return "dashboard"
    return "other"

for name, df in [("TRAIN", TRAIN), ("DEV", DEV)]:
    print(f"\n=== {name} (n={len(df)}) ===")
    for label_val, label_name in [(0, "LEGITIMATE"), (1, "PHISHING")]:
        sub = df[df["label"] == label_val]
        types = sub["url"].map(url_type)
        print(f"\n  {label_name} (n={len(sub)}):")
        vc = types.value_counts(normalize=True) * 100
        for t, pct in vc.items():
            print(f"    {t:20s}: {pct:6.2f}%  (n={int(pct/100*len(sub))})")

# Token frequency
import re
tokens = ["login", "signin", "account", "verify", "secure", "password", "payment", "auth", "paypal", "amazon", "google", "github", "microsoft", "dropbox"]
print("\n=== TOKEN FREQUENCY BY CLASS ===")
for name, df in [("TRAIN", TRAIN), ("DEV", DEV)]:
    print(f"\n--- {name} ---")
    for label_val, label_name in [(0, "LEGITIMATE"), (1, "PHISHING")]:
        sub = df[df["label"] == label_val]
        urls = sub["url"].astype(str).str.lower()
        print(f"  {label_name} (n={len(sub)}):")
        for tok in tokens:
            pct = (urls.str.contains(tok, regex=False)).mean() * 100
            print(f"    {tok:15s}: {pct:6.2f}%")

# Unique counts
print("\n=== UNIQUE COUNTS ===")
for name, df in [("TRAIN", TRAIN), ("DEV", DEV)]:
    print(f"\n--- {name} ---")
    for label_val, label_name in [(0, "LEGITIMATE"), (1, "PHISHING")]:
        sub = df[df["label"] == label_val]
        hosts = sub["url"].map(lambda u: u.split("://")[-1].split("/")[0].split(":")[0] if "://" in u else u.split("/")[0].split(":")[0])
        print(f"  {label_name}: URLs={len(sub)}, unique_URLs={sub['url'].nunique()}, unique_hosts={hosts.nunique()}")

# P(phishing | token)
print("\n=== P(PHISHING | token) in TRAIN ===")
for tok in tokens:
    has_tok = TRAIN["url"].astype(str).str.lower().str.contains(tok, regex=False)
    if has_tok.sum() > 0:
        p_phish = TRAIN.loc[has_tok, "label"].mean()
        print(f"  {tok:15s}: P(phishing|token)={p_phish:.4f}  (n={has_tok.sum()})")

# Save audit data
import json as _j
audit = {
    "train_n": len(TRAIN),
    "dev_n": len(DEV),
    "train_legit": int((TRAIN["label"]==0).sum()),
    "train_phish": int((TRAIN["label"]==1).sum()),
    "dev_legit": int((DEV["label"]==0).sum()),
    "dev_phish": int((DEV["label"]==1).sum()),
}
for name, df in [("train", TRAIN), ("dev", DEV)]:
    for lv, ln in [(0, "legit"), (1, "phish")]:
        sub = df[df["label"]==lv]
        types = sub["url"].map(url_type)
        audit[f"{name}_{ln}_types"] = {str(k): int(v) for k, v in types.value_counts().items()}
        audit[f"{name}_{ln}_n"] = len(sub)
with open(os.path.join(ROOT, "reports/technical/data_bias_audit_data.json"), "w") as f:
    _j.dump(audit, f, indent=2)
print("\nSaved data_bias_audit_data.json")
os.makedirs(os.path.join(ROOT, "reports/rootfix"), exist_ok=True)
print("Created reports/rootfix/")
