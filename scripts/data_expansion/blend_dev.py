import sys
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import roc_curve
from scipy.stats import rankdata

from src.evaluation.metrics import compute_metrics

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
DEV = pd.read_csv(f"{ROOT}/data/splits/DEV.csv")
y = DEV["label"].astype(int).values
urls = DEV["url"].astype(str).tolist()

base_art = joblib.load(f"{ROOT}/models/versions/M1_LR_HARDNEG.joblib")
base = base_art["model"].predict_proba(base_art["vectorizer"].transform(urls))[:, 1]
hyb = np.load(f"{ROOT}/reports/data_expansion_public/hybrid_dev_scores.npy")

cands = {}
for name in ["EXT_RANDOM_40K", "EXT_RANDOM_80K", "EXT_HARD_20K", "EXT_HARD_40K"]:
    art = joblib.load(f"{ROOT}/models/versions/candidates/{name}.joblib")
    cands[name] = art["model"].predict_proba(art["vectorizer"].transform(urls))[:, 1]


def at_fpr(s, target=0.01):
    fpr, tpr, thr = roc_curve(y, s)
    ok = fpr <= target
    t = float(thr[ok][int(np.argmax(tpr[ok]))])
    m = compute_metrics(y, s, threshold=t)
    return t, m["recall"], m["fpr"], m["precision"]


def report(name, s):
    m = compute_metrics(y, s, threshold=0.5)
    t, rec, fpr, prec = at_fpr(s)
    print(f"{name:30s} rec@.5={m['recall']:.4f} fpr@.5={m['fpr']:.4f} auc={m['roc_auc']:.4f} "
          f"rec@1%={rec:.4f} fpr@1%={fpr:.4f} thr={t:.4f}")


print("=== individual ===")
report("baseline", base)
report("hybrid", hyb)
for n, s in cands.items():
    report(n, s)

print("\n=== blends baseline + hybrid ===")
for w in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
    report(f"blend w_hyb={w}", (1 - w) * base + w * hyb)

print("\n=== rank blend baseline + hybrid ===")
rb = rankdata(base) / len(base)
rh = rankdata(hyb) / len(hyb)
for w in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
    report(f"rank blend w_hyb={w}", (1 - w) * rb + w * rh)

print("\n=== 3-way blends baseline + hybrid + best external ===")
for ext_name in ["EXT_RANDOM_40K", "EXT_HARD_20K"]:
    ext = cands[ext_name]
    for wb, wh, we in [(0.5, 0.25, 0.25), (0.4, 0.3, 0.3), (0.3, 0.4, 0.3),
                       (0.4, 0.4, 0.2), (0.5, 0.3, 0.2), (0.33, 0.33, 0.34)]:
        report(f"{ext_name} b{wb} h{wh} e{we}", wb * base + wh * hyb + we * ext)

print("\n=== 3-way rank blends ===")
for ext_name in ["EXT_RANDOM_40K", "EXT_HARD_20K"]:
    re = rankdata(cands[ext_name]) / len(cands[ext_name])
    for wb, wh, we in [(0.5, 0.25, 0.25), (0.4, 0.3, 0.3), (0.3, 0.4, 0.3),
                       (0.4, 0.4, 0.2), (0.5, 0.3, 0.2), (0.33, 0.33, 0.34)]:
        report(f"rank {ext_name} b{wb} h{wh} e{we}", wb * rb + wh * rh + we * re)
