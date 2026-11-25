"""Phase I — End-to-end evaluation: raw model vs allowlist policy layer."""
import sys, os
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

import numpy as np
import pandas as pd
import joblib
from src.policy.allowlist import AllowList
from src.evaluation.metrics import compute_metrics

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
DEV = pd.read_csv(os.path.join(ROOT, "data/splits/DEV.csv"))
ydev = DEV["label"].astype(int).values
Xdev_url = DEV["url"].astype(str).tolist()

art = joblib.load(os.path.join(ROOT, "models/versions/M1_LR.joblib"))
model = art["model"]; vec = art["vectorizer"]
sc = model.predict_proba(vec.transform(Xdev_url))[:, 1]

# Raw model at threshold 0.5
raw_pred = (sc >= 0.5).astype(int)
raw_m = compute_metrics(ydev, sc, threshold=0.5)
print("RAW model (thr=0.5):", {k: round(v,4) if isinstance(v,float) else v for k,v in raw_m.items() if k in ("accuracy","recall","fpr","precision")})

# Allowlist
al = AllowList(tranco_path=os.path.join(ROOT, "data/raw/tranco_top1m.csv.zip"), top_n=100000)
allowed = np.array([al.is_allowed(u) for u in Xdev_url])

# End-to-end: if allowed -> LEGITIMATE (0), else model prediction
e2e_pred = raw_pred.copy()
e2e_pred[allowed] = 0
# recompute metrics from e2e_pred
from sklearn.metrics import confusion_matrix
tn, fp, fn, tp = confusion_matrix(ydev, e2e_pred, labels=[0,1]).ravel()
e2e_recall = tp/(tp+fn)
e2e_fpr = fp/(fp+tn)
e2e_prec = tp/(tp+fp) if tp+fp else 0
e2e_acc = (tp+tn)/len(ydev)
print(f"\nAllowlist: {allowed.sum()} / {len(allowed)} DEV URLs allowed ({allowed.sum()/len(allowed)*100:.1f}%)")
print(f"END-TO-END (allowlist + model, thr=0.5): acc={e2e_acc:.4f} recall={e2e_recall:.4f} fpr={e2e_fpr:.4f} prec={e2e_prec:.4f}")
print(f"  confusion: tn={tn} fp={fp} fn={fn} tp={tp}")

# Also at optimized threshold 0.4937
thr = 0.4937
raw_pred2 = (sc >= thr).astype(int)
e2e_pred2 = raw_pred2.copy()
e2e_pred2[allowed] = 0
tn2, fp2, fn2, tp2 = confusion_matrix(ydev, e2e_pred2, labels=[0,1]).ravel()
print(f"\nEND-TO-END (allowlist + model, thr={thr}): recall={tp2/(tp2+fn2):.4f} fpr={fp2/(fp2+tn2):.4f} prec={tp2/(tp2+fp2):.4f} (tn={tn2} fp={fp2} fn={fn2} tp={tp2})")
