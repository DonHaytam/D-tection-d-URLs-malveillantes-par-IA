"""Hybrid model (M6) — FeatureUnion of char TF-IDF + numeric features + classifier."""
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.preprocessing import FunctionTransformer
from sklearn.linear_model import LogisticRegression
from ..features.character_features import make_char_tfidf
from ..features.feature_pipeline import build_numeric_features


def _numeric_transformer(urls):
    return build_numeric_features(urls).values


def build_hybrid(char_kwargs=None, C=1.0, class_weight="balanced", random_state=42):
    char_kwargs = char_kwargs or {"ngram_range": (3, 5), "min_df": 3, "max_features": 50000}
    numeric = FunctionTransformer(_numeric_transformer, validate=False)
    char = make_char_tfidf(**char_kwargs)
    features = FeatureUnion([
        ("char_tfidf", char),
        ("numeric", numeric),
    ])
    clf = LogisticRegression(C=C, class_weight=class_weight, solver="saga",
                             max_iter=2000, random_state=random_state, n_jobs=-1)
    return Pipeline([("features", features), ("clf", clf)])
