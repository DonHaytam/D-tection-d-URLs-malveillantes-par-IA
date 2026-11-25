"""Predictor wrapper: loads a trained artifact and exposes predict()."""
import json, os, time, sys
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

import joblib
import numpy as np
from src.features.feature_pipeline import build_numeric_features
from src.policy.decision_policy import decide

ROOT = "D:/openhands/projects/v2/phishing_ai_master"


class Predictor:
    def __init__(self, model_path, metadata_path=None):
        obj = joblib.load(model_path)
        if isinstance(obj, dict):
            self.model = obj.get("model")
            self.vectorizer = obj.get("vectorizer")
            self.feature_names = obj.get("feature_names")
            self.kind = obj.get("kind")
            self.scaler = obj.get("scaler")
            self.numeric_feature_names = obj.get("numeric_feature_names")
        else:
            self.model = obj
            self.vectorizer = None
            self.feature_names = None
            self.kind = None
            self.scaler = None
            self.numeric_feature_names = None
        self.tranco_rank = {}
        if self.kind == "hybrid_char_numeric":
            from src.features.hybrid_reputation_features import load_tranco_rank
            self.tranco_rank = load_tranco_rank(ROOT)
        self.metadata = {}
        if metadata_path and os.path.exists(metadata_path):
            with open(metadata_path) as f:
                self.metadata = json.load(f)
        self.low = self.metadata.get("low_threshold", 0.25)
        self.high = self.metadata.get("high_threshold", 0.75)
        self.version = self.metadata.get("model_version", "V0")

    def _score(self, urls):
        # hybrid char + numeric + Tranco reputation model
        if self.kind == "hybrid_char_numeric":
            from src.features.hybrid_reputation_features import transform_with_artifact
            art = {"vectorizer": self.vectorizer, "scaler": self.scaler,
                   "numeric_feature_names": self.numeric_feature_names}
            X = transform_with_artifact(art, urls, self.tranco_rank)
            return self.model.predict_proba(X)[:, 1]
        # char tfidf models
        if self.vectorizer is not None:
            X = self.vectorizer.transform(urls)
            if hasattr(self.model, "predict_proba"):
                return self.model.predict_proba(X)[:, 1]
            return self.model.decision_function(X)
        # pipeline models (hybrid) handle urls directly
        if hasattr(self.model, "predict_proba") and not hasattr(self.model, "transform"):
            # could be a sklearn Pipeline that accepts raw text
            try:
                return self.model.predict_proba(urls)[:, 1]
            except Exception:
                pass
        # numeric feature models
        X = build_numeric_features(urls)
        if self.feature_names is not None:
            X = X[self.feature_names]
        if hasattr(self.model, "predict_proba"):
            return self.model.predict_proba(X)[:, 1]
        return self.model.decision_function(X)

    def predict_one(self, url):
        t0 = time.time()
        sc = self._score([url])
        score = float(np.asarray(sc).ravel()[0])
        verdict = decide(score, self.low, self.high)
        return {
            "url": url,
            "verdict": verdict,
            "score": score,
            "model_version": self.version,
            "thresholds": {"low": self.low, "high": self.high},
            "processing_time_ms": round((time.time() - t0) * 1000, 2),
        }
