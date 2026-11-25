"""Weighted soft-voting ensemble for live A/B testing.

M1 is the deployed logistic-regression baseline.  M2 is a calibrated linear
SVM and M5 is an XGBoost model on numeric URL features.  The weighted average
is intentionally simple and interpretable; it does not retrain or overwrite
any production artifact.
"""
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

import joblib
import numpy as np

from src.features.feature_pipeline import build_numeric_features
from src.policy.decision_policy import decide

ROOT = "D:/openhands/projects/v2/phishing_ai_master"


class EnsemblePredictor:
    def __init__(self, baseline_predictor, m2_path=None, m5_path=None,
                 weights=(0.5, 0.3, 0.2)):
        self.baseline = baseline_predictor
        self.weights = tuple(float(w) for w in weights)
        self.m2_path = m2_path or os.path.join(ROOT, "models/versions/M2_SVM.joblib")
        self.m5_path = m5_path or os.path.join(ROOT, "models/versions/M5_XGBOOST.joblib")
        self._m2 = None
        self._m5 = None
        self._load()

    def _load(self):
        try:
            if os.path.exists(self.m2_path):
                self._m2 = joblib.load(self.m2_path)
        except Exception:
            self._m2 = None
        try:
            if os.path.exists(self.m5_path):
                self._m5 = joblib.load(self.m5_path)
        except Exception:
            self._m5 = None

    @property
    def available(self):
        return self._m2 is not None or self._m5 is not None

    @property
    def version(self):
        parts = [self.baseline.version]
        if self._m2 is not None:
            parts.append("M2")
        if self._m5 is not None:
            parts.append("M5")
        return "ENSEMBLE[" + "+".join(parts) + "]"

    def _scores(self, url):
        out = {}
        base = self.baseline._score([url])
        out["M1"] = float(np.asarray(base).ravel()[0])
        if self._m2 is not None:
            try:
                vec = self._m2["vectorizer"]
                model = self._m2["model"]
                X = vec.transform([url])
                out["M2"] = float(model.predict_proba(X)[:, 1][0])
            except Exception:
                out["M2"] = out["M1"]
        if self._m5 is not None:
            try:
                X = build_numeric_features([url])
                X = X[self._m5["feature_names"]]
                out["M5"] = float(self._m5["model"].predict_proba(X)[:, 1][0])
            except Exception:
                out["M5"] = out["M1"]
        return out

    def predict_one(self, url):
        t0 = time.time()
        scores = self._scores(url)
        weights = {name: w for name, w in zip(("M1", "M2", "M5"), self.weights) if name in scores}
        total = sum(weights.values()) or 1.0
        score = sum(scores[name] * w for name, w in weights.items()) / total
        score = max(0.0, min(1.0, float(score)))
        verdict = decide(score, self.baseline.low, self.baseline.high)
        return {
            "url": url,
            "verdict": verdict,
            "score": score,
            "model_version": self.version,
            "thresholds": {"low": self.baseline.low, "high": self.baseline.high},
            "processing_time_ms": round((time.time() - t0) * 1000, 2),
            "component_scores": {k: round(v, 6) for k, v in scores.items()},
            "weights": {k: round(v / total, 4) for k, v in weights.items()},
        }
