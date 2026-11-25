"""Explainability module: logistic-regression coefficient contributions.

For the deployed char TF-IDF model the contribution of a feature is
``tfidf_value * coefficient``.  Positive contributions push the URL toward
phishing, negative contributions toward legitimate.  The module also builds a
small non-overlapping annotation of the URL for the frontend.
"""
import html
import os
import sys

sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

import joblib
import numpy as np

ROOT = "D:/openhands/projects/v2/phishing_ai_master"


def _annotate(url, terms, max_terms=8):
    """Return URL segments with non-overlapping highlighted terms."""
    lower = str(url).lower()
    spans = []
    for label, term in terms[:max_terms]:
        t = str(term).strip().lower()
        if len(t) < 3 or len(t) > 40:
            continue
        start = 0
        while True:
            idx = lower.find(t, start)
            if idx < 0:
                break
            end = idx + len(t)
            if not any(idx < s_end and end > s_start for s_start, s_end, _ in spans):
                spans.append((idx, end, label))
            start = idx + 1
    spans.sort(key=lambda x: x[0])
    segments = []
    cursor = 0
    for start, end, label in spans:
        if start > cursor:
            segments.append({"text": str(url)[cursor:start], "signal": None})
        segments.append({"text": str(url)[start:end], "signal": label})
        cursor = end
    if cursor < len(str(url)):
        segments.append({"text": str(url)[cursor:], "signal": None})
    return segments


def get_top_contributing_features(url, model_artifact, top_n=10):
    """Return top contributing char n-grams, numeric signals and annotations."""
    model = model_artifact["model"]
    vec = model_artifact["vectorizer"]
    feature_names = vec.get_feature_names_out()
    X = vec.transform([url])
    coefs = model.coef_[0] if hasattr(model, "coef_") else None
    if coefs is None:
        return {"phishing_signals": [], "legitimate_signals": [],
                "method": "not_available", "annotated_url": [{"text": str(url), "signal": None}]}
    coefs = np.asarray(coefs).ravel()
    # Hybrid artifacts append numeric features after the char n-grams.
    char_coefs = coefs[:len(feature_names)]
    contributions = X.toarray()[0] * char_coefs
    top_pos_idx = np.argsort(contributions)[-top_n:][::-1]
    top_neg_idx = np.argsort(contributions)[:top_n]
    pos = [(str(feature_names[i]), round(float(contributions[i]), 4))
           for i in top_pos_idx if contributions[i] > 0]
    neg = [(str(feature_names[i]), round(float(contributions[i]), 4))
           for i in top_neg_idx if contributions[i] < 0]

    # Deduplicate near-identical n-grams while keeping the strongest ones.
    def dedupe(items, limit=8):
        out, seen = [], set()
        for term, val in items:
            key = term.strip()
            if not key or key in seen:
                continue
            seen.add(key)
            out.append([term, val])
            if len(out) >= limit:
                break
        return out

    pos = dedupe(pos)
    neg = dedupe(neg)

    numeric = []
    numeric_names = model_artifact.get("numeric_feature_names")
    if model_artifact.get("kind") == "hybrid_char_numeric" and numeric_names:
        try:
            from src.features.hybrid_reputation_features import numeric_frame, load_tranco_rank
            N = numeric_frame([url], load_tranco_rank(ROOT))
            num_vals = N[numeric_names].values.astype(float).ravel()
            num_coefs = coefs[len(feature_names):len(feature_names) + len(numeric_names)]
            num_contrib = num_vals * num_coefs
            for i in np.argsort(np.abs(num_contrib))[-6:][::-1]:
                numeric.append([str(numeric_names[i]), round(float(num_contrib[i]), 4)])
        except Exception:
            numeric = []

    terms = [("phishing", t) for t, _ in pos] + [("legitimate", t) for t, _ in neg]
    return {
        "method": "logistic_regression_coefficients",
        "phishing_signals": pos,
        "legitimate_signals": neg,
        "numeric_signals": numeric,
        "annotated_url": _annotate(url, terms),
        "summary": (
            f"{len(pos)} signal(aux) phishing et {len(neg)} signal(aux) legitimes "
            "ont influence la decision."
        ),
    }


if __name__ == "__main__":
    art = joblib.load(os.path.join(ROOT, "models/versions/M1_LR_HARDNEG.joblib"))
    sample = "https://www.paypal.com/login"
    print("URL:", html.escape(sample))
    print(get_top_contributing_features(sample, art, top_n=8))
