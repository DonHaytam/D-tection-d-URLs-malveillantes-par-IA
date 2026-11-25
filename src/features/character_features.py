"""Character-level features: TF-IDF over character n-grams."""
from sklearn.feature_extraction.text import TfidfVectorizer


def make_char_tfidf(analyzer="char", ngram_range=(3, 5), min_df=3, max_features=50000):
    """Factory for a character TF-IDF vectorizer."""
    return TfidfVectorizer(
        analyzer=analyzer,
        ngram_range=ngram_range,
        min_df=min_df,
        max_features=max_features,
        lowercase=True,
        sublinear_tf=True,
    )
