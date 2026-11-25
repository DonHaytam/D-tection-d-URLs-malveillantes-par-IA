"""Shared platform detection and platform-aware numeric features.

Kept separate from training scripts so importing it never starts training.
"""
import re

import numpy as np
import pandas as pd

from src.data.provenance import registrable_domain
from src.data.validation import extract_components
from src.features.feature_pipeline import build_numeric_features
from hybrid_features import numeric_frame

SHORTENERS = {
    "bit.ly", "t.co", "goo.gl", "tinyurl.com", "is.gd", "buff.ly", "ow.ly", "rb.gy",
    "cutt.ly", "shorturl.at", "rebrand.ly", "tiny.cc", "lnkd.in", "t.ly", "s.id",
    "v.gd", "qr.ae", "adf.ly", "sh.st", "clck.ru", "shorturl.com", "tiny.one",
    "urlz.fr", "x.co", "me2.do", "j.mp", "bit.do", "soo.gd", "trib.al", "dlvr.it",
    "ift.tt", "wp.me", "flip.it", "po.st", "snip.ly", "surl.li", "shorte.st",
    "tr.ee", "urlgeni.us", "tinyurl.io", "rebrandly.com", "short.io", "bl.ink",
}
FREE_HOSTS = {
    "3utilities.com", "ocry.com", "mefound.com", "000webhostapp.com", "weebly.com",
    "wixsite.com", "blogspot.com", "wordpress.com", "github.io", "gitlab.io",
    "netlify.app", "vercel.app", "herokuapp.com", "glitch.me", "repl.co",
    "firebaseapp.com", "web.app", "pages.dev", "workers.dev", "rf.gd", "42web.io",
    "infinityfree.net", "epizy.com", "byethost.com", "freehostia.com", "awardspace.com",
    "000space.com", "x10.bz", "in.net", "pe.hu", "esy.es", "hol.es", "16mb.com",
    "my.id", "web.id", "site88.net", "freewebhostingarea.com", "atw.hu", "thats.im",
    "youdontcare.com", "babinet.cz", "home.pl", "pp.ua", "pp.ru",
}
DOC_HOSTS = {
    "docs.google.com", "drive.google.com", "forms.gle", "script.google.com",
    "sites.google.com", "forms.office.com", "outlook.office.com", "onedrive.live.com",
    "sharepoint.com", "notion.so", "notion.site", "airtable.com", "typeform.com",
    "jotform.com", "cognitoforms.com", "paperform.co", "forms.app", "surveyheart.com",
    "sendgrid.net", "mailchimp.com", "list-manage.com",
}
CLOUD_HOSTS = {
    "amazonaws.com", "cloudfront.net", "azurewebsites.net", "appspot.com",
    "googleusercontent.com", "blogspot.com", "windows.net", "digitaloceanspaces.com",
    "storage.googleapis.com", "r2.dev", "backblazeb2.com", "linodeobjects.com",
}


def platform_of(url):
    try:
        host = extract_components(url)["host"].lower()
    except Exception:
        return "", ""
    rd = registrable_domain(host)
    if any(host == d or host.endswith("." + d) for d in DOC_HOSTS):
        return "doc", rd
    if rd in SHORTENERS:
        return "shortener", rd
    if any(rd == d or rd.endswith("." + d) for d in FREE_HOSTS):
        return "free", rd
    if any(rd == d or rd.endswith("." + d) for d in CLOUD_HOSTS):
        return "cloud", rd
    return "", rd


def platform_frame(urls, tranco_rank, with_flags=True):
    base = numeric_frame(urls, tranco_rank)
    platforms, rds = [], []
    for u in urls:
        p, rd = platform_of(u)
        platforms.append(p)
        rds.append(rd)
    platform = np.array([1.0 if p else 0.0 for p in platforms])
    is_doc = np.array([1.0 if p == "doc" else 0.0 for p in platforms])
    is_short = np.array([1.0 if p == "shortener" else 0.0 for p in platforms])
    is_free = np.array([1.0 if p == "free" else 0.0 for p in platforms])
    is_cloud = np.array([1.0 if p == "cloud" else 0.0 for p in platforms])
    auth = base["auth_path_flag"].values
    tok = base["auth_token_count"].values
    query = base["has_query"].values
    path_depth = base["path_depth"].values
    keep = 1.0 - platform
    for col in ("tranco_present", "tranco_top10k", "tranco_top100k", "tranco_top1m"):
        base[col] = base[col].values * keep
    ranks = np.array([tranco_rank.get(d, 0) for d in rds], dtype=float) * keep
    base["tranco_log_rank"] = np.where(ranks > 0, np.log1p(ranks), 0.0)
    present = base["tranco_present"].values
    top10k = base["tranco_top10k"].values
    base["auth_x_top10k"] = auth * top10k
    base["auth_x_present"] = auth * present
    base["auth_x_absent"] = auth * (1.0 - present)
    base["token_x_present"] = tok * present
    base["token_x_absent"] = tok * (1.0 - present)
    if with_flags:
        extra = pd.DataFrame({
            "platform_flag": platform,
            "platform_doc": is_doc,
            "platform_shortener": is_short,
            "platform_free": is_free,
            "platform_cloud": is_cloud,
            "platform_x_auth": platform * auth,
            "platform_x_token": platform * tok,
            "platform_x_query": platform * query,
            "platform_x_pathdepth": platform * path_depth,
            "free_x_auth": is_free * auth,
            "short_x_query": is_short * query,
            "doc_x_auth": is_doc * auth,
        })
        base = pd.concat([base.reset_index(drop=True), extra.reset_index(drop=True)], axis=1)
    return base


def url_path(u):
    s = str(u)
    try:
        rest = s.split("://", 1)[1]
    except Exception:
        rest = s.lstrip("/")
    if "/" in rest:
        return "/" + rest.split("/", 1)[1]
    return "/"


PLATFORM_TYPES = ["free", "shortener", "doc", "cloud"]
PLATFORM_NUMERIC_COLS = [
    "url_length", "host_length", "path_length", "query_length", "n_dots",
    "n_hyphens", "n_digits", "n_special", "n_subdomains", "n_path_segments",
    "suspicious_token_count", "char_entropy", "digit_ratio", "special_ratio",
    "scheme_https", "scheme_http", "has_port", "is_ip_host", "subdomain_depth",
    "has_query", "query_param_count", "has_fragment", "path_depth",
    "has_at_symbol", "has_double_slash_in_path", "encoded_char_count",
    "host_has_hyphen", "tld_length",
]


def platform_numeric(urls):
    base = build_numeric_features(urls)
    out = base[PLATFORM_NUMERIC_COLS].copy()
    types = [platform_of(u)[0] for u in urls]
    for t in PLATFORM_TYPES:
        out[f"platform_{t}"] = [1.0 if x == t else 0.0 for x in types]
    return out
