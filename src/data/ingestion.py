"""URL ingestion helpers for the phishing AI Master 2 project.

Loads raw sources into pandas DataFrames with a common schema:
    url, label, source, collection_date
"""
import json
import os
import zipfile
import pandas as pd

ROOT = "D:/openhands/projects/v2/phishing_ai_master"


def load_hf_urls(path=None):
    """Load the HuggingFace ealvaradob/phishing-dataset urls.json."""
    if path is None:
        path = os.path.join(ROOT, "data", "raw", "hf_phishing", "urls.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data).rename(columns={"text": "url"})
    df["label"] = df["label"].astype(int)
    df["source"] = "huggingface_ealvaradob"
    df["collection_date"] = "unknown (dataset publication date not verified)"
    return df[["url", "label", "source", "collection_date"]]


def load_tranco(path=None, n=None):
    """Load Tranco top-1m.csv (rank, domain) as legitimate URLs (label 0)."""
    if path is None:
        path = os.path.join(ROOT, "data", "raw", "tranco_top1m.csv.zip")
    with zipfile.ZipFile(path) as z:
        with z.open("top-1m.csv") as f:
            df = pd.read_csv(f, header=None, names=["rank", "domain"])
    if n is not None:
        df = df.head(n)
    df["url"] = "https://" + df["domain"].astype(str).str.strip()
    df["label"] = 0
    df["source"] = "tranco_top1m"
    df["collection_date"] = "current (top-1m list, downloaded 2026-11-24)"
    return df[["url", "label", "source", "collection_date"]]


def load_phishtank_nontruncated(path=None):
    """Load PhishTank offline XLSX, keeping only non-truncated phishing URLs."""
    if path is None:
        path = os.path.join(ROOT, "data", "raw", "phishtank_offline_1.xlsx")
    df = pd.read_excel(path)
    df = df[df["VALID"].astype(str).str.upper().str.contains("VALID", na=False)].copy()
    df = df.rename(columns={"Phish": "url"})
    df["url"] = df["url"].astype(str).str.strip()
    # keep only URLs that do NOT end with "..." (truncated)
    df = df[~df["url"].str.endswith("...", na=False)]
    df = df[df["url"].str.startswith("http", na=False)]
    df["label"] = 1
    df["source"] = "phishtank_zenodo_8371046"
    df["collection_date"] = "2015-12 (submitted, historical)"
    return df[["url", "label", "source", "collection_date"]]
