"""Provenance helpers: build the dataset manifest with required columns."""
import os
import re
import pandas as pd
from .validation import extract_components, normalize_url


MULTI_PART_SUFFIXES = {
    "co.uk", "org.uk", "ac.uk", "gov.uk", "com.au", "net.au", "org.au",
    "co.nz", "com.br", "com.cn", "co.jp", "com.mx",
}


def registrable_domain(host):
    host = (host or "").lower().strip(".")
    if not host:
        return ""
    # IP address host
    if re_ip(host):
        return host
    parts = host.split(".")
    if len(parts) <= 2:
        return host
    suffix2 = ".".join(parts[-2:])
    if suffix2 in MULTI_PART_SUFFIXES and len(parts) >= 3:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def re_ip(h):
    import re
    return bool(re.match(r"^\d{1,3}(\.\d{1,3}){3}$", h))


def tld_of(host):
    host = (host or "").lower().strip(".")
    if not host or re_ip(host):
        return ""
    parts = host.split(".")
    if len(parts) < 2:
        return ""
    # multi-part
    suffix2 = ".".join(parts[-2:])
    if suffix2 in MULTI_PART_SUFFIXES:
        return suffix2
    return parts[-1]


def build_manifest(df, dataset_version="v1"):
    """Add manifest columns to a DataFrame that already has url, label, source, collection_date."""
    out = df.copy()
    # compute components
    comps = out["url"].map(extract_components)
    out["scheme"] = [c["scheme"] for c in comps]
    out["host"] = [c["host"] for c in comps]
    out["path"] = [c["path"] for c in comps]
    out["query"] = [c["query"] for c in comps]
    out["fragment"] = [c["fragment"] for c in comps]
    out["domain"] = out["host"]
    out["registrable_domain"] = [registrable_domain(h) for h in out["host"]]
    out["tld"] = [tld_of(h) for h in out["host"]]
    out["dataset_version"] = dataset_version
    out["url"] = [normalize_url(u) for u in out["url"]]
    cols = ["url", "label", "source", "collection_date", "domain",
            "registrable_domain", "tld", "scheme", "path", "query",
            "fragment", "dataset_version"]
    result = pd.DataFrame({c: out[c] for c in cols})
    return result
