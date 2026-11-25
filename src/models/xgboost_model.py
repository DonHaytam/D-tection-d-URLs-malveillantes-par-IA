"""XGBoost model (M5) — optional, loaded from vendor_libs."""
try:
    import sys
    sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")
    from xgboost import XGBClassifier
    AVAILABLE = True
except Exception:
    XGBClassifier = None
    AVAILABLE = False


def build_xgboost(n_estimators=300, learning_rate=0.1, max_depth=6,
                  random_state=42, n_jobs=-1):
    if not AVAILABLE:
        raise RuntimeError("XGBoost not available")
    return XGBClassifier(
        n_estimators=n_estimators, learning_rate=learning_rate,
        max_depth=max_depth, random_state=random_state, n_jobs=n_jobs,
        use_label_encoder=False, eval_metric="logloss",
        tree_method="hist",
    )
