"""Audit likely label noise in DEV phishing using passive URL-only evidence.

No URL is fetched. Evidence used:
- Tranco top-1M rank (popular domain)
- PhishTank offline exact URL / registrable-domain match (weak positive)
- URL-only benign/suspicious heuristics (auth tokens, IP, punycode, shortener,
  free host, path depth, query, suspicious TLD)
"""
import json
import os
import re
import sys
import zipfile

sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

import numpy as np
import pandas as pd
import joblib

from src.data.provenance import registrable_domain
from src.data.validation import extract_components

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
OUT = os.path.join(ROOT, "reports", "data_expansion_public")

DEV = pd.read_csv(os.path.join(ROOT, "data/splits/DEV.csv"))
urls = DEV["url"].astype(str)
y = DEV["label"].astype(int).values

# Tranco
with zipfile.ZipFile(os.path.join(ROOT, "data/raw/tranco_top1m.csv.zip")) as z:
    with z.open("top-1m.csv") as f:
        tranco = pd.read_csv(f, header=None, names=["rank", "domain"])
rank = {str(d).lower(): int(r) for r, d in zip(tranco["rank"], tranco["domain"])}
DEV["tranco_rank"] = DEV["registrable_domain"].astype(str).str.lower().map(rank)

# PhishTank (optional: heavy xlsx; set SKIP_PHISHTANK=1 to skip)
PHISHTANK_SKIPPED = os.environ.get("SKIP_PHISHTANK") == "1"
if PHISHTANK_SKIPPED:
    print("Skipping PhishTank (SKIP_PHISHTANK=1)")
    DEV["in_phishtank"] = False
    DEV["pt_domain"] = False
else:
    print("Loading PhishTank...")
    pt = pd.read_excel(os.path.join(ROOT, "data/raw/phishtank_offline_1.xlsx"))
    pt = pt[pt["VALID"].astype(str).str.upper().str.contains("VALID", na=False)]
    pt_urls = set(pt["Phish"].astype(str).str.strip().str.lower())
    pt_domains = set()
    for u in pt_urls:
        try:
            host = u.split("://", 1)[1].split("/", 1)[0].split(":")[0].lower()
        except Exception:
            continue
        pt_domains.add(registrable_domain(host))
    print(f"PhishTank URLs={len(pt_urls)} domains={len(pt_domains)}")
    DEV["in_phishtank"] = urls.str.lower().isin(pt_urls)
    DEV["pt_domain"] = DEV["registrable_domain"].astype(str).str.lower().isin(pt_domains)

AUTH_RE = re.compile(r"login|signin|sign-in|sign_in|logon|auth|account|verify|verification|password|passwd|oauth|register|signup|sign-up|security|checkout|payment|billing|secure|session|sso|saml|openid|mfa|2fa", re.I)
SHORTENERS = {"bit.ly", "t.co", "goo.gl", "tinyurl.com", "is.gd", "buff.ly", "ow.ly", "rb.gy", "cutt.ly",
              "shorturl.at", "rebrand.ly", "tiny.cc", "lnkd.in", "t.ly", "s.id", "v.gd", "qr.ae", "adf.ly",
              "sh.st", "clck.ru", "shorturl.com", "tiny.one", "urlz.fr", "x.co", "me2.do"}
FREE_HOSTS = {"3utilities.com", "ocry.com", "mefound.com", "000webhostapp.com", "weebly.com", "wixsite.com",
              "blogspot.com", "wordpress.com", "github.io", "gitlab.io", "netlify.app", "vercel.app",
              "herokuapp.com", "glitch.me", "repl.co", "firebaseapp.com", "web.app", "pages.dev",
              "workers.dev", "rf.gd", "42web.io", "infinityfree.net", "epizy.com", "byethost.com",
              "freehostia.com", "awardspace.com", "000space.com", "x10.bz", "in.net", "pe.hu", "esy.es",
              "hol.es", "16mb.com", "my.id", "web.id", "site88.net", "freewebhostingarea.com"}
DOC_HOSTS = {"docs.google.com", "drive.google.com", "forms.gle", "script.google.com", "sites.google.com",
             "forms.office.com", "outlook.office.com", "onedrive.live.com", "sharepoint.com", "notion.so",
             "notion.site", "airtable.com", "typeform.com", "jotform.com", "cognitoforms.com", "paperform.co",
             "forms.app", "surveyheart.com"}
SUSPICIOUS_TLDS = {"tk", "ml", "ga", "cf", "gq", "top", "xyz", "club", "online", "site", "website", "space",
                   "live", "icu", "buzz", "click", "link", "work", "support", "review", "country", "stream",
                   "download", "win", "bid", "loan", "date", "faith", "party", "science", "men", "cricket"}

rows = []
for _, r in DEV.iterrows():
    u = str(r["url"])
    try:
        c = extract_components(u)
        host = c["host"].lower()
    except Exception:
        host = ""
    rd = registrable_domain(host)
    path = ""
    try:
        rest = u.split("://", 1)[1]
        path = rest.split("/", 1)[1] if "/" in rest else ""
    except Exception:
        pass
    low = u.lower()
    rows.append({
        "url": u,
        "host": host,
        "rd": rd,
        "tld": host.rsplit(".", 1)[-1] if "." in host else "",
        "auth_token": int(bool(AUTH_RE.search(low))),
        "is_ip": int(bool(re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", host))),
        "is_punycode": int(host.startswith("xn--") or ".xn--" in host),
        "is_shortener": int(rd in SHORTENERS),
        "is_free_host": int(any(rd == d or rd.endswith("." + d) for d in FREE_HOSTS)),
        "is_doc_host": int(any(host == d or host.endswith("." + d) for d in DOC_HOSTS)),
        "path_depth": path.count("/") if path else 0,
        "has_query": int("?" in u),
        "suspicious_tld": int((host.rsplit(".", 1)[-1] if "." in host else "") in SUSPICIOUS_TLDS),
    })
F = pd.DataFrame(rows)
DEV = pd.concat([DEV.reset_index(drop=True), F.drop(columns=["url"])], axis=1)
DEV["benign_looking"] = (
    (DEV["tranco_rank"].notna()) & (DEV["tranco_rank"] <= 10000) &
    (DEV["auth_token"] == 0) & (DEV["is_ip"] == 0) & (DEV["is_punycode"] == 0) &
    (DEV["is_shortener"] == 0) & (DEV["is_free_host"] == 0) & (DEV["is_doc_host"] == 0) &
    (DEV["path_depth"] <= 1) & (DEV["has_query"] == 0) & (DEV["suspicious_tld"] == 0)
)
DEV["suspicious_any"] = ((DEV["auth_token"] == 1) | (DEV["is_ip"] == 1) | (DEV["is_punycode"] == 1) |
                         (DEV["is_shortener"] == 1) | (DEV["is_free_host"] == 1) | (DEV["is_doc_host"] == 1) |
                         (DEV["suspicious_tld"] == 1))

phish = DEV[DEV.label == 1]
print(f"\nDEV phishing n={len(phish)}")
if PHISHTANK_SKIPPED:
    print("  PhishTank matching: SKIPPED")
else:
    print(f"  in PhishTank exact: {phish.in_phishtank.sum()} ({phish.in_phishtank.mean()*100:.1f}%)")
    print(f"  in PhishTank domain: {phish.pt_domain.sum()} ({phish.pt_domain.mean()*100:.1f}%)")
print(f"  Tranco top10k: {((phish.tranco_rank<=10000)).sum()} ({((phish.tranco_rank<=10000)).mean()*100:.1f}%)")
print(f"  benign-looking (top10k, no auth/IP/puny/short/free/doc, path<=1, no query): {phish.benign_looking.sum()} ({phish.benign_looking.mean()*100:.1f}%)")
print(f"  no suspicious feature at all: {(~phish.suspicious_any).sum()} ({(~phish.suspicious_any).mean()*100:.1f}%)")
if not PHISHTANK_SKIPPED:
    print(f"  benign-looking & not in PhishTank: {(phish.benign_looking & ~phish.in_phishtank).sum()}")

print("\nBenign-looking phishing candidates (top 60):")
for _, r in phish[phish.benign_looking].head(60).iterrows():
    print(f"  tranco={int(r.tranco_rank):6d} pt={int(r.in_phishtank)} {r.url[:130]}")

print("\nNo-suspicious-feature phishing (top 60):")
for _, r in phish[~phish.suspicious_any].head(60).iterrows():
    print(f"  tranco={r.tranco_rank if pd.notna(r.tranco_rank) else 'nan':>8} pt={int(r.in_phishtank)} {r.url[:130]}")

summary = {
    "dev_phishing": int(len(phish)),
    "phishtank_matching": "skipped" if PHISHTANK_SKIPPED else "performed",
    "tranco_top10k": int((phish.tranco_rank <= 10000).sum()),
    "benign_looking": int(phish.benign_looking.sum()),
    "no_suspicious_feature": int((~phish.suspicious_any).sum()),
}
if not PHISHTANK_SKIPPED:
    summary["in_phishtank_exact"] = int(phish.in_phishtank.sum())
    summary["in_phishtank_domain"] = int(phish.pt_domain.sum())
    summary["benign_looking_not_phishtank"] = int((phish.benign_looking & ~phish.in_phishtank).sum())
with open(os.path.join(OUT, "dev_label_noise_audit.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)
print("\nSaved", os.path.join(OUT, "dev_label_noise_audit.json"))
