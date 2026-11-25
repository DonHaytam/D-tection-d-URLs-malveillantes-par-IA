"""Gradient Boosting model (M4) — numeric lexical/structural features."""
from sklearn.ensemble import GradientBoostingClassifier


def build_gradient_boosting(n_estimators=200, learning_rate=0.1, max_depth=3,
                            random_state=42):
    return GradientBoostingClassifier(
        n_estimators=n_estimators, learning_rate=learning_rate,
        max_depth=max_depth, random_state=random_state,
    )
