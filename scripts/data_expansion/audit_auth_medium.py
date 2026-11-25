import sys
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")
import pandas as pd
import re

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
p = pd.read_csv(f"{ROOT}/data/integrated/external_pool.csv",
                usecols=["url", "label", "registrable_domain", "source"])

CORE = r"login|signin|sign-in|sign_in|logon|register|signup|sign-up|oauth|openid|saml|sso|mfa|2fa|password|passwd|verify|verification|authentification|connexion|account|auth"
rx = re.compile(rf"/(?:[^/]*(?:{CORE})[^/]*)", re.I)
BAD = re.compile(r"author|authority|accounting|accountant|accountmanager|accountsupport|registered|registration-?id|session[s]?/|sessions?\.|service", re.I)

def path_of(u):
    try:
        r = str(u).split("://", 1)[1]
        return "/" + (r.split("/", 1)[1] if "/" in r else "")
    except Exception:
        return ""

def is_medium_auth(u):
    path = path_of(u)
    for m in rx.finditer(path):
        seg = m.group(0)
        if BAD.search(seg):
            continue
        # require the token to be at a segment boundary-ish
        return 1
    return 0

p["medium_auth"] = p["url"].map(is_medium_auth)
for lab, name in [(0, "legit"), (1, "phish")]:
    sub = p[(p.label == lab) & (p.medium_auth == 1)]
    print(f"{name}: n={len(sub)} domains={sub.registrable_domain.nunique()} sources={sub.source.value_counts().to_dict()}")
print("\nlegit samples:")
for u in p[(p.label == 0) & (p.medium_auth == 1)].url.head(120):
    print("  ", u[:160])
