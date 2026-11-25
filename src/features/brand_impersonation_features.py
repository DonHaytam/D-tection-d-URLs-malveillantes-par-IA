"""Brand impersonation features: detect brand token != registered domain."""
BRANDS = [
    "paypal", "amazon", "apple", "google", "microsoft", "facebook",
    "instagram", "netflix", "dropbox", "github", "linkedin", "twitter",
    "whatsapp", "outlook", "ebay", "chase", "wellsfargo", "citibank",
    "bankofamerica", "usaa", "steam", "spotify", "adobe",
]


def brand_impersonation_features(url):
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
    # brand in registered domain (official)
    feats["brand_in_regdomain"] = 1 if any(b in reg_domain for b in BRANDS) else 0
    # brand in subdomain (potential impersonation)
    feats["brand_in_subdomain"] = 1 if any(b in subdomain for b in BRANDS) else 0
    # brand in path
    feats["brand_in_path"] = 1 if any(b in path_query for b in BRANDS) else 0
    # brand mismatch: brand appears in subdomain/path but NOT in registered domain
    feats["brand_mismatch"] = 1 if ((feats["brand_in_subdomain"] or feats["brand_in_path"]) and not feats["brand_in_regdomain"]) else 0
    # brand in regdomain AND elsewhere (legitimate brand URL)
    feats["brand_official"] = 1 if (feats["brand_in_regdomain"] and not feats["brand_mismatch"]) else 0
    # count of brand tokens
    feats["num_brand_tokens"] = sum(1 for b in BRANDS if b in u)
    return feats
