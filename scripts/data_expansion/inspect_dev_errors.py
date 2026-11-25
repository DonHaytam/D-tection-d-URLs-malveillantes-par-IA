import sys
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")
import numpy as np
import pandas as pd
import joblib

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
DEV = pd.read_csv(f"{ROOT}/data/splits/DEV.csv")
hyb = np.load(f"{ROOT}/reports/data_expansion_public/hybrid_dev_scores.npy")
base_art = joblib.load(f"{ROOT}/models/versions/M1_LR_HARDNEG.joblib")
base = base_art["model"].predict_proba(base_art["vectorizer"].transform(DEV["url"].astype(str).tolist()))[:, 1]
DEV["base"] = base
DEV["hyb"] = hyb

# Tranco ranks
from src.features.hybrid_reputation_features import load_tranco_rank
tr = load_tranco_rank(ROOT)
DEV["tranco"] = DEV["registrable_domain"].astype(str).str.lower().map(tr)
DEV["auth"] = DEV["url"].str.contains(r"login|signin|sign-in|auth|account|verify|password|oauth|register|signup|security|checkout|payment|billing|secure", case=False, regex=True).astype(int)

print("=== DEV phishing missed by hybrid @0.903 (score < 0.903) ===")
fn = DEV[(DEV.label == 1) & (DEV.hyb < 0.903)].sort_values("hyb")
print(f"count={len(fn)} / {(DEV.label==1).sum()}")
for _, r in fn.head(60).iterrows():
    print(f"  hyb={r.hyb*100:6.2f}% base={r.base*100:6.2f}% tranco={r.tranco} auth={r.auth} src={r.source[:18]:18s} {r.url[:130]}")

print("\n=== DEV legitimate flagged by hybrid @0.903 (score >= 0.903) ===")
fp = DEV[(DEV.label == 0) & (DEV.hyb >= 0.903)].sort_values("hyb", ascending=False)
print(f"count={len(fp)} / {(DEV.label==0).sum()}")
for _, r in fp.head(40).iterrows():
    print(f"  hyb={r.hyb*100:6.2f}% base={r.base*100:6.2f}% tranco={r.tranco} auth={r.auth} src={r.source[:18]:18s} {r.url[:130]}")

print("\n=== DEV legitimate in review (0.25<=hyb<0.903) ===")
rev = DEV[(DEV.label == 0) & (DEV.hyb >= 0.25) & (DEV.hyb < 0.903)].sort_values("hyb", ascending=False)
print(f"count={len(rev)} / {(DEV.label==0).sum()}")
for _, r in rev.head(20).iterrows():
    print(f"  hyb={r.hyb*100:6.2f}% base={r.base*100:6.2f}% tranco={r.tranco} auth={r.auth} {r.url[:120]}")

print("\n=== DEV phishing detected only via review (0.25<=hyb<0.903) ===")
revp = DEV[(DEV.label == 1) & (DEV.hyb >= 0.25) & (DEV.hyb < 0.903)].sort_values("hyb", ascending=False)
print(f"count={len(revp)} / {(DEV.label==1).sum()}")
for _, r in revp.head(20).iterrows():
    print(f"  hyb={r.hyb*100:6.2f}% base={r.base*100:6.2f}% tranco={r.tranco} auth={r.auth} {r.url[:120]}")

# source breakdown
print("\n=== by source ===")
for src, g in DEV.groupby("source"):
    print(f"{src}: n={len(g)} phish={(g.label==1).sum()} legit={(g.label==0).sum()}")
