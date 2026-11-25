"""Keyword position features: aggregate keyword position features (memory-efficient)."""
BRAND_KEYWORDS = [
    "login", "signin", "sign-in", "auth", "authentication", "account",
    "accounts", "password", "reset", "forgot", "verify", "security",
    "bank", "payment", "confirm", "update", "paypal", "amazon", "apple",
    "google", "microsoft", "dropbox", "github",
]


def keyword_position_features(url):
    u = str(url).lower()
    if "://" in u:
        rest = u.split("://", 1)[1]
        host = rest.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]
        path_query = rest.split("/", 1)[1] if "/" in rest else ""
    else:
        host = u.split("/", 1)[0].split("?", 1)[0]
        path_query = u.split("/", 1)[1] if "/" in u else ""
    host = host.split(":")[0]
    parts = host.split(".")
    reg_domain = ".".join(parts[-2:]) if len(parts) >= 2 else host
    subdomain = ".".join(parts[:-2]) if len(parts) > 2 else ""
    query = path_query.split("?", 1)[1] if "?" in path_query else ""
    path = path_query.split("?", 1)[0]

    feats = {}
    feats["any_kw_in_regdomain"] = 1 if any(kw in reg_domain for kw in BRAND_KEYWORDS) else 0
    feats["any_kw_in_subdomain"] = 1 if any(kw in subdomain for kw in BRAND_KEYWORDS) else 0
    feats["any_kw_in_path"] = 1 if any(kw in path for kw in BRAND_KEYWORDS) else 0
    feats["any_kw_in_query"] = 1 if any(kw in query for kw in BRAND_KEYWORDS) else 0
    feats["kw_mismatch_subdomain"] = 1 if (feats["any_kw_in_subdomain"] and not feats["any_kw_in_regdomain"]) else 0
    feats["kw_mismatch_path"] = 1 if (feats["any_kw_in_path"] and not feats["any_kw_in_regdomain"]) else 0
    feats["n_kw_regdomain"] = sum(1 for kw in BRAND_KEYWORDS if kw in reg_domain)
    feats["n_kw_subdomain"] = sum(1 for kw in BRAND_KEYWORDS if kw in subdomain)
    feats["n_kw_path"] = sum(1 for kw in BRAND_KEYWORDS if kw in path)
    feats["n_kw_query"] = sum(1 for kw in BRAND_KEYWORDS if kw in query)
    return feats
