"""Shared feature builders for the hybrid char + numeric + Tranco model."""
import re
import zipfile

import numpy as np
import pandas as pd
from scipy.sparse import hstack, csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler

from src.features.feature_pipeline import build_numeric_features
from src.data.provenance import registrable_domain
from src.data.validation import extract_components

AUTH_RE = re.compile(
    r"(?:^|/)(login|signin|sign-in|sign_in|auth|account|accounts|verify|verification|"
    r"password|oauth|register|signup|sign-up|security|checkout|payment|billing|"
    r"wp-login\.php|login\.php|signin\.php)(?:/|$|[.?])", re.I)
AUTH_TOKEN_RE = re.compile(
    r"login|signin|sign-in|auth|account|verify|password|oauth|register|signup|"
    r"security|checkout|payment|billing|secure", re.I)


def is_auth_path(u):
    try:
        p = str(u).split("://", 1)[1]
        path = p.split("/", 1)[1] if "/" in p else ""
        return int(bool(AUTH_RE.search("/" + path.split("?")[0])))
    except Exception:
        return 0


def load_tranco_rank(root):
    with zipfile.ZipFile(f"{root}/data/raw/tranco_top1m.csv.zip") as z:
        with z.open("top-1m.csv") as f:
            tranco = pd.read_csv(f, header=None, names=["rank", "domain"])
    return {str(d).lower(): int(r) for r, d in zip(tranco["rank"], tranco["domain"])}


def numeric_frame(urls, tranco_rank):
    base = build_numeric_features(urls)
    rds = []
    auths = []
    toks = []
    for u in urls:
        try:
            host = extract_components(u)["host"]
        except Exception:
            host = ""
        rds.append(registrable_domain(host))
        auths.append(is_auth_path(u))
        toks.append(len(AUTH_TOKEN_RE.findall(str(u).lower())))
    ranks = np.array([tranco_rank.get(d, 0) for d in rds], dtype=float)
    present = (ranks > 0).astype(float)
    log_rank = np.where(ranks > 0, np.log1p(ranks), 0.0)
    top10k = ((ranks > 0) & (ranks <= 10000)).astype(float)
    top100k = ((ranks > 0) & (ranks <= 100000)).astype(float)
    auth = np.array(auths, dtype=float)
    tok = np.array(toks, dtype=float)
    extra = pd.DataFrame({
        "tranco_present": present,
        "tranco_log_rank": log_rank,
        "tranco_top10k": top10k,
        "tranco_top100k": top100k,
        "tranco_top1m": present,
        "auth_path_flag": auth,
        "auth_token_count": tok,
        "auth_x_top10k": auth * top10k,
        "auth_x_present": auth * present,
        "auth_x_absent": auth * (1.0 - present),
        "token_x_present": tok * present,
        "token_x_absent": tok * (1.0 - present),
    })
    return pd.concat([base.reset_index(drop=True), extra.reset_index(drop=True)], axis=1)


def transform_with_artifact(art, urls, tranco_rank):
    vec = art["vectorizer"]
    scaler = art["scaler"]
    X_char = vec.transform(urls)
    N = numeric_frame(urls, tranco_rank)
    N_s = scaler.transform(N.values.astype(np.float32))
    return hstack([X_char, csr_matrix(N_s)]).tocsr()
