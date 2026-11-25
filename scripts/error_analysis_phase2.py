"""Phase 2 — Advanced error analysis."""
import sys, os
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

import numpy as np
import pandas as pd
import joblib
from src.features.lexical_features import lexical_features
from src.features.structural_features import structural_features

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
DEV = pd.read_csv(os.path.join(ROOT, "data/splits/DEV.csv"))
art = joblib.load(os.path.join(ROOT, "models/versions/M1_LR_HARDNEG.joblib"))
model = art["model"]; vec = art["vectorizer"]
scores = model.predict_proba(vec.transform(DEV["url"].astype(str).tolist()))[:, 1]
DEV = DEV.copy()
DEV["score"] = scores
DEV["pred"] = (scores >= 0.5).astype(int)
DEV["error_type"] = "correct"
DEV.loc[(DEV["label"]==0)&(DEV["pred"]==1), "error_type"] = "FP"
DEV.loc[(DEV["label"]==1)&(DEV["pred"]==0), "error_type"] = "FN"

def host_of(u):
    h = u.split("://")[-1].split("/")[0].split(":")[0] if "://" in u else u.split("/")[0].split(":")[0]
    return h.lower()

DEV["host"] = DEV["url"].map(host_of)
DEV["tld"] = DEV["host"].map(lambda h: h.split(".")[-1].lower() if "." in h else "(none)")
DEV["url_len"] = DEV["url"].str.len()
DEV["n_subdomains"] = DEV["host"].map(lambda h: h.count("."))
DEV["has_ip"] = DEV["host"].map(lambda h: all(c.isdigit() or c=="." for c in h) and "." in h)
DEV["is_http"] = DEV["url"].str.startswith("http://").astype(int)

# Error by TLD
print("=== FPR by TLD (top 10) ===")
legit = DEV[DEV["label"]==0]
g = legit.groupby("tld").agg(n=("url","size"), fp=("error_type", lambda x: (x=="FP").sum()))
g["fpr"] = g["fp"]/g["n"]
print(g.sort_values("n", ascending=False).head(10).to_string())

# Error by source
print("\n=== Error by source ===")
for src in DEV["source"].unique():
    sub = DEV[DEV["source"]==src]
    fp = ((sub["label"]==0)&(sub["pred"]==1)).sum()
    fn = ((sub["label"]==1)&(sub["pred"]==0)).sum()
    print(f"  {src}: n={len(sub)} FP={fp} FN={fn} FPR={fp/(sub['label']==0).sum():.4f}")

# Error by URL length
print("\n=== FN by URL length bucket ===")
phish = DEV[DEV["label"]==1]
phish["len_bucket"] = pd.cut(phish["url_len"], bins=[0,30,50,80,120,200,10000], labels=["0-30","31-50","51-80","81-120","121-200","200+"])
gb = phish.groupby("len_bucket", observed=True).agg(n=("url","size"), fn=("error_type", lambda x: (x=="FN").sum()))
gb["fnr"] = gb["fn"]/gb["n"]
print(gb.to_string())

# Save
os.makedirs(os.path.join(ROOT, "reports/tables"), exist_ok=True)
DEV[["url","label","pred","score","error_type","source","tld","url_len","host"]].to_csv(
    os.path.join(ROOT, "reports/tables/error_analysis_advanced.csv"), index=False)
print("\nSaved error_analysis_advanced.csv")

# Summary for report
fp_count = (DEV["error_type"]=="FP").sum()
fn_count = (DEV["error_type"]=="FN").sum()
print(f"\nTotal: FP={fp_count}, FN={fn_count}, Correct={len(DEV)-fp_count-fn_count}")
print(f"FP rate (of legit): {fp_count/(DEV['label']==0).sum():.4f}")
print(f"FN rate (of phish): {fn_count/(DEV['label']==1).sum():.4f}")
