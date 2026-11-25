"""Phase H — Calibration: compare Platt (sigmoid) vs isotonic on M1 (DEV)."""
import sys, os, json
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

import numpy as np
import pandas as pd
import joblib
from sklearn.calibration import CalibratedClassifierCV
from src.evaluation.metrics import compute_metrics, expected_calibration_error

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
DEV = pd.read_csv(os.path.join(ROOT, "data/splits/DEV.csv"))
ydev = DEV["label"].astype(int).values
Xdev_url = DEV["url"].astype(str).tolist()

art = joblib.load(os.path.join(ROOT, "models/versions/M1_LR.joblib"))
model = art["model"]; vec = art["vectorizer"]
Xdev = vec.transform(Xdev_url)
sc_raw = model.predict_proba(Xdev)[:, 1]

# Platt scaling (sigmoid) via CalibratedClassifierCV on a copy
from sklearn.linear_model import LogisticRegression
# Fit a logistic regression on the raw scores (Platt)
platt = LogisticRegression(C=1e10, solver="lbfgs", max_iter=1000)
platt.fit(sc_raw.reshape(-1, 1), ydev)
sc_platt = platt.predict_proba(sc_raw.reshape(-1, 1))[:, 1]

# Isotonic via sklearn
from sklearn.isotonic import IsotonicRegression
iso = IsotonicRegression(out_of_bounds="clip")
iso.fit(sc_raw, ydev)
sc_iso = iso.predict(sc_raw)

for name, sc in [("raw", sc_raw), ("platt", sc_platt), ("isotonic", sc_iso)]:
    m = compute_metrics(ydev, sc)
    m["ece"] = expected_calibration_error(ydev, sc)
    print(f"{name:10s}: brier={m['brier']:.4f} ece={m['ece']:.4f} auc={m['roc_auc']:.4f} (brier lower=better)")

# Save calibrated model artifact
joblib.dump({"model": model, "vectorizer": vec, "platt": platt, "isotonic": iso},
            os.path.join(ROOT, "models/versions/M1_LR_calibrated.joblib"))
print("Saved calibrated artifact.")
# Save platt params
import json as _j
with open(os.path.join(ROOT, "models/versions/M1_LR_calibration.json"), "w") as f:
    _j.dump({"platt_coef": float(platt.coef_[0][0]), "platt_intercept": float(platt.intercept_[0]),
             "method": "platt"}, f, indent=2)
print("Done.")
