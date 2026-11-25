"""Phase C — False positive analysis: group FPs by feature."""
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
art = joblib.load(os.path.join(ROOT, "models/versions/M1_LR.joblib"))
model = art["model"]; vec = art["vectorizer"]
sc = model.predict_proba(vec.transform(DEV["url"].astype(str).tolist()))[:, 1]
DEV = DEV.copy()
DEV["score"] = sc
DEV["pred"] = (sc >= 0.5).astype(int)
fp_df = DEV[(DEV["label"]==0)&(DEV["pred"]==1)].copy()

# build feature frames
lex = pd.DataFrame([lexical_features(u) for u in fp_df["url"]])
struct = pd.DataFrame([structural_features(u) for u in fp_df["url"]])
feat = pd.concat([lex, struct], axis=1)
feat["source"] = fp_df["source"].values
feat["tld"] = fp_df["url"].map(lambda u: u.split("://")[-1].split("/")[0].split(".")[-1].lower() if "." in u.split("://")[-1].split("/")[0] else "(none)")

# Summary by source
print("FP count:", len(fp_df))
print("\n=== Mean feature values: FP vs all legit ===")
all_legit = DEV[DEV["label"]==0]
lex_all = pd.DataFrame([lexical_features(u) for u in all_legit["url"]])
struct_all = pd.DataFrame([structural_features(u) for u in all_legit["url"]])
feat_all = pd.concat([lex_all, struct_all], axis=1)

for col in feat.columns:
    if col in ("source","tld"):
        continue
    print(f"  {col:28s}  FP_mean={feat[col].mean():8.3f}  ALLLEGIT_mean={feat_all[col].mean():8.3f}")

# Save
os.makedirs(os.path.join(ROOT, "reports/tables"), exist_ok=True)
feat.describe().to_csv(os.path.join(ROOT, "reports/tables/fp_feature_summary.csv"))
print("\nSaved fp_feature_summary.csv")
