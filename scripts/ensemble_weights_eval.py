import sys, json
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import roc_auc_score, roc_curve
from src.features.feature_pipeline import build_numeric_features
from src.evaluation.metrics import compute_metrics

R = "D:/openhands/projects/v2/phishing_ai_master"
dev = pd.read_csv(f"{R}/data/splits/DEV.csv", usecols=["url", "label"])
urls = dev.url.astype(str).tolist()
y = dev.label.astype(int).values

m1 = joblib.load(f"{R}/models/versions/M1_LR_HARDNEG.joblib")
s1 = m1["model"].predict_proba(m1["vectorizer"].transform(urls))[:, 1]
m2 = joblib.load(f"{R}/models/versions/M2_SVM.joblib")
s2 = m2["model"].predict_proba(m2["vectorizer"].transform(urls))[:, 1]
m5 = joblib.load(f"{R}/models/versions/M5_XGBOOST.joblib")
s5 = m5["model"].predict_proba(build_numeric_features(urls)[m5["feature_names"]])[:, 1]

print("M1", compute_metrics(y, s1), roc_auc_score(y, s1))
print("M2", compute_metrics(y, s2), roc_auc_score(y, s2))
print("M5", compute_metrics(y, s5), roc_auc_score(y, s5))

for w in [(1.0, 0, 0), (0.7, 0.2, 0.1), (0.6, 0.3, 0.1), (0.5, 0.3, 0.2), (0.5, 0.5, 0), (0.7, 0.3, 0)]:
    s = w[0]*s1 + w[1]*s2 + w[2]*s5
    m = compute_metrics(y, s)
    fpr, tpr, thr = roc_curve(y, s)
    ok = fpr <= 0.01
    rec1 = float(tpr[ok][np.argmax(tpr[ok])]) if ok.any() else None
    print(w, "rec", round(m["recall"],4), "fpr", round(m["fpr"],4), "auc", round(roc_auc_score(y,s),4), "rec@1%", round(rec1,4) if rec1 else None)
