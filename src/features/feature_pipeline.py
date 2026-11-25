"""Feature pipeline: combines lexical, structural and character TF-IDF features."""
import numpy as np
import pandas as pd
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import FunctionTransformer
from .lexical_features import lexical_features
from .structural_features import structural_features
from .character_features import make_char_tfidf


def _lexical_matrix(urls):
    return pd.DataFrame([lexical_features(u) for u in urls])


def _structural_matrix(urls):
    return pd.DataFrame([structural_features(u) for u in urls])


def build_numeric_features(urls):
    """Return a DataFrame of lexical+structural numeric features."""
    lex = _lexical_matrix(urls)
    struct = _structural_matrix(urls)
    return pd.concat([lex, struct], axis=1)


def build_char_tfidf(urls, **kwargs):
    v = make_char_tfidf(**kwargs)
    X = v.fit_transform(urls)
    return v, X
