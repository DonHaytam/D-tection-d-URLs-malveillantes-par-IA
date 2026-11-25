"""Model registry — maps model id to builder."""
from .logistic_regression import build_logistic_regression
from .linear_svm import build_linear_svm
from .random_forest import build_random_forest
from .gradient_boosting import build_gradient_boosting
from .xgboost_model import build_xgboost, AVAILABLE as XGB_AVAILABLE
from .hybrid_model import build_hybrid


REGISTRY = {
    "M1_LR": build_logistic_regression,
    "M2_SVM": build_linear_svm,
    "M3_RF": build_random_forest,
    "M4_GB": build_gradient_boosting,
    "M6_HYBRID": build_hybrid,
}
if XGB_AVAILABLE:
    REGISTRY["M5_XGBOOST"] = build_xgboost


def available_models():
    return list(REGISTRY.keys())
