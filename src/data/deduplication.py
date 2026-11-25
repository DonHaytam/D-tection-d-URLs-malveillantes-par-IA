"""Deduplication helpers (exact + normalized) for the phishing AI project."""
import hashlib
from .validation import normalize_url


def url_hash(url, normalized=True):
    u = normalize_url(url) if normalized else str(url).strip()
    return hashlib.sha256(u.encode("utf-8")).hexdigest()


def exact_dedup(df, col="url"):
    """Drop exact duplicate URLs (raw string)."""
    before = len(df)
    out = df.drop_duplicates(subset=[col], keep="first").copy()
    return out, before - len(out)


def normalized_dedup(df, col="url"):
    """Drop duplicates based on normalized URL."""
    before = len(df)
    df = df.copy()
    df["_norm"] = df[col].map(normalize_url)
    df = df.drop_duplicates(subset=["_norm"], keep="first")
    df = df.drop(columns=["_norm"])
    return df, before - len(df)
