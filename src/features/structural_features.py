"""Structural features for URLs."""
import re
from .url_parser import parse_url, count_query_params


IP_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")


def is_ip_host(host):
    return bool(IP_RE.match(host or ""))


def structural_features(url):
    p = parse_url(url)
    host = p["host"]
    feats = {}
    feats["scheme_https"] = 1 if p["scheme"] == "https" else 0
    feats["scheme_http"] = 1 if p["scheme"] == "http" else 0
    feats["has_port"] = 1 if p["port"] is not None else 0
    feats["is_ip_host"] = 1 if is_ip_host(host) else 0
    feats["subdomain_depth"] = host.count(".") if host else 0
    feats["has_query"] = 1 if p["query"] else 0
    feats["query_param_count"] = count_query_params(p["query"])
    feats["has_fragment"] = 1 if p["fragment"] else 0
    feats["path_depth"] = p["path"].count("/") if p["path"] else 0
    feats["has_at_symbol"] = 1 if "@" in str(url) else 0
    feats["has_double_slash_in_path"] = 1 if "//" in p["path"] else 0
    feats["encoded_char_count"] = str(url).count("%")
    feats["host_has_hyphen"] = 1 if "-" in host else 0
    feats["tld_length"] = len(host.split(".")[-1]) if "." in host else 0
    return feats
