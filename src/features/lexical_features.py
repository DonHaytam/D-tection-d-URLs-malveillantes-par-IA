"""Lexical features for URLs."""
import math
import re
from collections import Counter

SUSPICIOUS_TOKENS = [
    "login", "signin", "verify", "account", "update", "secure", "bank",
    "password", "confirm", "paypal", "apple", "microsoft", "google",
    "amazon", "ebay", "webscr", "cmd", "token", "auth",
]


def char_entropy(s):
    if not s:
        return 0.0
    c = Counter(s)
    n = len(s)
    return -sum((v / n) * math.log2(v / n) for v in c.values())


def lexical_features(url):
    u = str(url)
    host = u
    if "://" in u:
        host = u.split("://", 1)[1].split("/", 1)[0]
    path = ""
    if "://" in u:
        rest = u.split("://", 1)[1]
        if "/" in rest:
            path = rest.split("/", 1)[1]
    query = ""
    if "?" in u:
        query = u.split("?", 1)[1]
    low = u.lower()
    feats = {}
    feats["url_length"] = len(u)
    feats["host_length"] = len(host)
    feats["path_length"] = len(path)
    feats["query_length"] = len(query)
    feats["n_dots"] = u.count(".")
    feats["n_hyphens"] = u.count("-")
    feats["n_digits"] = sum(c.isdigit() for c in u)
    feats["n_special"] = sum(not c.isalnum() for c in u)
    feats["n_subdomains"] = host.count(".") - 1 if host.count(".") >= 1 else 0
    feats["n_path_segments"] = path.count("/") if path else 0
    feats["suspicious_token_count"] = sum(low.count(t) for t in SUSPICIOUS_TOKENS)
    feats["char_entropy"] = char_entropy(u)
    feats["digit_ratio"] = feats["n_digits"] / max(len(u), 1)
    feats["special_ratio"] = feats["n_special"] / max(len(u), 1)
    return feats
