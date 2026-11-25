"""Inspect external hard examples selected by the deployed baseline.

Checks whether high-scoring legitimate URLs and low-scoring phishing URLs are
plausible hard cases or likely label noise, using Tranco and PhishTank as weak
external evidence (no network access).
"""
import json
import os
import sys
import zipfile

sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

import numpy as np
import pandas as pd
import joblib

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
OUT = os.path.join(ROOT, "reports", "data_expansion_public")
os.makedirs(OUT, exist_ok=True)

def score_chunks(art, urls, chunk=20000):
    model, vec = art["model"], art["vectorizer"]
    out = []
    for i in range(0, len(urls), chunk):
        out.append(model.predict_proba(vec.transform(urls[i:i+chunk]))[:, 1])
    return np.concatenate(out)

# Tranco
with zipfile.ZipFile(os.path.join(ROOT, "data/raw/tranco_top1m.csv.zip")) as z:
    with z.open("top-1m.csv") as f:
        tranco = pd.read_csv(f, header=None, names=["rank", "domain"])
rank = {str(d).lower(): int(r) for r, d in zip(tranco["rank"], tranco["domain"])}

# PhishTank (weak positive evidence; historical, incomplete)
print("Loading PhishTank...")
pt = pd.read_excel(os.path.join(ROOT, "data/raw/phishtank_offline_1.xlsx"))
pt = pt[pt["VALID"].astype(str).str.upper().str.contains("VALID", na=False)]
pt_urls = set(pt["Phish"].astype(str).str.strip().str.lower())
pt_domains = set()
for u in pt_urls:
    try:
        host = u.split("://", 1)[1].split("/", 1)[0].split(":")[0].lower()
    except Exception:
        continue
    parts = host.split(".")
    if len(parts) >= 2:
        pt_domains.add(".".join(parts[-2:]))
print(f"PhishTank valid URLs: {len(pt_urls)}, domains: {len(pt_domains)}")

EXT = pd.read_csv(os.path.join(ROOT, "data/integrated/external_train.csv"))
art = joblib.load(os.path.join(ROOT, "models/versions/M1_LR_HARDNEG.joblib"))
print("Scoring external train...")
EXT = EXT.copy()
EXT["base_score"] = score_chunks(art, EXT["url"].astype(str).tolist())
EXT["tranco_rank"] = EXT["registrable_domain"].astype(str).str.lower().map(rank)
EXT["in_tranco"] = EXT["tranco_rank"].notna()
EXT["in_phishtank"] = EXT["url"].astype(str).str.lower().isin(pt_urls)
EXT["pt_domain"] = EXT["registrable_domain"].astype(str).str.lower().isin(pt_domains)

legit = EXT[EXT["label"] == 0]
phish = EXT[EXT["label"] == 1]
hard_legit = legit[legit["base_score"] >= 0.5]
hard_phish = phish[phish["base_score"] < 0.5]

summary = {
    "external_train": {
        "rows": int(len(EXT)),
        "legit": int(len(legit)), "phish": int(len(phish)),
        "hard_legit_score_ge_0.5": int(len(hard_legit)),
        "hard_phish_score_lt_0.5": int(len(hard_phish)),
    },
    "hard_legit": {
        "rows": int(len(hard_legit)),
        "in_tranco": int(hard_legit["in_tranco"].sum()),
        "in_phishtank": int(hard_legit["in_phishtank"].sum()),
        "pt_domain": int(hard_legit["pt_domain"].sum()),
        "source_counts": hard_legit["source"].value_counts().to_dict(),
        "auth_path": int(hard_legit["is_auth_path"].sum()),
    },
    "hard_phish": {
        "rows": int(len(hard_phish)),
        "in_tranco": int(hard_phish["in_tranco"].sum()),
        "in_phishtank": int(hard_phish["in_phishtank"].sum()),
        "pt_domain": int(hard_phish["pt_domain"].sum()),
        "source_counts": hard_phish["source"].value_counts().to_dict(),
        "auth_path": int(hard_phish["is_auth_path"].sum()),
    },
}

print(json.dumps(summary, indent=2))
print("\nTop hard legitimate (score>=0.5):")
for _, r in hard_legit.sort_values("base_score", ascending=False).head(25).iterrows():
    print(f"  {r['base_score']*100:6.2f}% tranco={r['tranco_rank']} pt={r['pt_domain']} "
          f"src={r['source']} {r['url'][:110]}")
print("\nBottom hard phishing (score<0.5):")
for _, r in hard_phish.sort_values("base_score", ascending=True).head(25).iterrows():
    print(f"  {r['base_score']*100:6.2f}% tranco={r['tranco_rank']} pt={r['pt_domain']} "
          f"src={r['source']} {r['url'][:110]}")

hard_legit.head(500).to_csv(os.path.join(OUT, "hard_legit_sample.csv"), index=False)
hard_phish.head(500).to_csv(os.path.join(OUT, "hard_phish_sample.csv"), index=False)
with open(os.path.join(OUT, "hard_examples.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)
print(f"\nSaved {OUT}/hard_examples.json")
