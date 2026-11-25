"""Enhanced lexical features including brand-token position features (aggregated only)."""
BRAND_TOKENS = [
    "paypal", "apple", "microsoft", "google", "amazon", "ebay", "facebook",
    "instagram", "netflix", "bank", "chase", "wellsfargo", "citibank",
    "usaa", "dropbox", "linkedin", "twitter", "whatsapp", "outlook",
]


def brand_position_features(url):
    u = str(url).lower()
    if "://" in u:
        host = u.split("://", 1)[1].split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]
    else:
        host = u.split("/", 1)[0].split("?", 1)[0]
    host = host.split(":")[0]
    parts = host.split(".")
    reg_domain = ".".join(parts[-2:]) if len(parts) >= 2 else host
    subdomain = ".".join(parts[:-2]) if len(parts) > 2 else ""
    path_query = ""
    if "://" in u:
        rest = u.split("://", 1)[1]
        if "/" in rest:
            path_query = rest.split("/", 1)[1]
    elif "/" in u:
        path_query = u.split("/", 1)[1]
    feats = {}
    feats["any_brand_in_regdomain"] = 1 if any(t in reg_domain for t in BRAND_TOKENS) else 0
    feats["any_brand_in_subdomain"] = 1 if any(t in subdomain for t in BRAND_TOKENS) else 0
    feats["any_brand_in_path"] = 1 if any(t in path_query for t in BRAND_TOKENS) else 0
    feats["brand_in_subdomain_not_regdomain"] = 1 if (feats["any_brand_in_subdomain"] and not feats["any_brand_in_regdomain"]) else 0
    feats["brand_in_path_not_regdomain"] = 1 if (feats["any_brand_in_path"] and not feats["any_brand_in_regdomain"]) else 0
    return feats
