"""Logistic Regression model (M1) — character TF-IDF representation."""
from sklearn.linear_model import LogisticRegression


def build_logistic_regression(C=1.0, penalty="l2", class_weight="balanced",
                             solver="saga", max_iter=2000, random_state=42):
    return LogisticRegression(
        C=C, penalty=penalty, class_weight=class_weight,
        solver=solver, max_iter=max_iter, random_state=random_state,
        n_jobs=-1,
    )
