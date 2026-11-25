"""Random Forest model (M3) — numeric lexical/structural features."""
from sklearn.ensemble import RandomForestClassifier


def build_random_forest(n_estimators=300, max_depth=None, min_samples_leaf=1,
                        class_weight="balanced", random_state=42, n_jobs=-1):
    return RandomForestClassifier(
        n_estimators=n_estimators, max_depth=max_depth,
        min_samples_leaf=min_samples_leaf, class_weight=class_weight,
        random_state=random_state, n_jobs=n_jobs,
    )
