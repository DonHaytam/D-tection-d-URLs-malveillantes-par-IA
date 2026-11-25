"""Phase A — Full diagnostic audit for FPR reduction."""
import sys, os, json
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

import numpy as np
import pandas as pd
import joblib
from src.evaluation.metrics import compute_metrics, expected_calibration_error
from src.features.feature_pipeline import build_numeric_features
from src.features.lexical_features import lexical_features
from src.features.structural_features import structural_features

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
DEV = pd.read_csv(os.path.join(ROOT, "data/splits/DEV.csv"))
Xdev_url = DEV["url"].astype(str).tolist()
ydev = DEV["label"].astype(int).values

# Load M1 (best candidate)
art = joblib.load(os.path.join(ROOT, "models/versions/M1_LR.joblib"))
model = art["model"]
vec = art["vectorizer"]

# scores
sc = model.predict_proba(vec.transform(Xdev_url))[:, 1]
pred = (sc >= 0.5).astype(int)

# confusion
from sklearn.metrics import confusion_matrix
tn, fp, fn, tp = confusion_matrix(ydev, pred, labels=[0,1]).ravel()
print("CONFUSION: tn=%d fp=%d fn=%d tp=%d" % (tn,fp,fn,tp))
print("FPR=%.4f  FNR=%.4f  Precision=%.4f  Recall=%.4f" % (fp/(fp+tn), fn/(fn+tp), tp/(tp+fp) if tp+fp else 0, tp/(tp+fn)))

# Attach predictions to DEV
DEV = DEV.copy()
DEV["score"] = sc
DEV["pred"] = pred
DEV["fp"] = ((DEV["label"]==0) & (DEV["pred"]==1)).astype(int)
DEV["fn"] = ((DEV["label"]==1) & (DEV["pred"]==0)).astype(int)

# helper: tld
def tld_of(u):
    h = u.split("://")[-1].split("/")[0].split(":")[0] if "://" in u else u.split("/")[0].split(":")[0]
    parts = h.split(".")
    return parts[-1].lower() if len(parts) >= 2 and parts[-1].isalpha() and len(parts[-1]) <= 6 else "(none/ip)"
DEV["tld"] = DEV["url"].map(tld_of)
DEV["url_len"] = DEV["url"].str.len()

# FPR by TLD (legit only)
legit = DEV[DEV["label"]==0]
print("\n--- FPR by TLD (top 15 by count) ---")
g = legit.groupby("tld").agg(n=("url","size"), fp=("fp","sum"))
g["fpr"] = g["fp"]/g["n"]
g = g.sort_values("n", ascending=False).head(15)
print(g.to_string())

# FPR by URL length bucket
print("\n--- FPR by URL length bucket ---")
legit["len_bucket"] = pd.cut(legit["url_len"], bins=[0,20,40,60,80,120,200,10000], labels=["0-20","21-40","41-60","61-80","81-120","121-200","200+"])
gb = legit.groupby("len_bucket", observed=True).agg(n=("url","size"), fp=("fp","sum"))
gb["fpr"] = gb["fp"]/gb["n"]
print(gb.to_string())

# FPR by source
print("\n--- FPR by source ---")
gs = legit.groupby("source").agg(n=("url","size"), fp=("fp","sum"))
gs["fpr"] = gs["fp"]/gs["n"]
print(gs.to_string())

# Top false positive URLs
print("\n--- Top 20 false positives (highest score) ---")
fp_df = DEV[(DEV["label"]==0)&(DEV["pred"]==1)].sort_values("score", ascending=False).head(20)
for _, r in fp_df.iterrows():
    print(f"  score={r['score']:.3f} src={r['source']} url={r['url'][:80]}")

# Top false negatives
print("\n--- Top 20 false negatives (lowest score) ---")
fn_df = DEV[(DEV["label"]==1)&(DEV["pred"]==0)].sort_values("score").head(20)
for _, r in fn_df.iterrows():
    print(f"  score={r['score']:.3f} src={r['source']} url={r['url'][:80]}")

# Save diagnostic data
os.makedirs(os.path.join(ROOT, "reports/technical"), exist_ok=True)
out = {
    "confusion": {"tn":int(tn),"fp":int(fp),"fn":int(fn),"tp":int(tp)},
    "fpr": float(fp/(fp+tn)), "fnr": float(fn/(fn+tp)),
    "precision": float(tp/(tp+fp)) if tp+fp else 0.0,
    "recall": float(tp/(tp+fn)),
    "n_dev": int(len(DEV)),
}
with open(os.path.join(ROOT, "reports/technical/fpr_diagnostic_data.json"), "w") as f:
    json.dump(out, f, indent=2)
# save fp/fn csvs
fp_df.to_csv(os.path.join(ROOT, "reports/tables/false_positives_dev.csv"), index=False)
fn_df.to_csv(os.path.join(ROOT, "reports/tables/false_negatives_dev.csv"), index=False)
g.to_csv(os.path.join(ROOT, "reports/tables/fpr_by_tld.csv"))
gb.to_csv(os.path.join(ROOT, "reports/tables/fpr_by_length.csv"))
gs.to_csv(os.path.join(ROOT, "reports/tables/fpr_by_source.csv"))
print("\nDiagnostic data saved.")
