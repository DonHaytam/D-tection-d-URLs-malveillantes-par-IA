import sys
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")
import pandas as pd
import re

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
p = pd.read_csv(f"{ROOT}/data/integrated/external_pool.csv",
                usecols=["url", "label", "registrable_domain", "source"])

TOKEN = r"login|signin|sign-in|sign_in|logon|auth|account|verify|verification|password|passwd|oauth|register|signup|sign-up|security|session|sso|saml|openid|mfa|2fa"
rx = re.compile(rf"/(?:[^/]*(?:{TOKEN})[^/]*)", re.I)
# stricter: token must be a whole word-ish segment part, avoid author/authority
rx2 = re.compile(rf"/(?:[^/]*(?:{TOKEN})[^/]*)", re.I)

def path_of(u):
    try:
        r = str(u).split("://", 1)[1]
        return "/" + (r.split("/", 1)[1] if "/" in r else "")
    except Exception:
        return ""

p["path"] = p["url"].map(path_of)
m = p["path"].str.contains(rx, regex=True)
print("permissive: total", int(m.sum()), "legit", int(((p.label == 0) & m).sum()),
      "phish", int(((p.label == 1) & m).sum()))
print("legit domains", p[(p.label == 0) & m].registrable_domain.nunique())
print(p[(p.label == 0) & m].source.value_counts().to_dict())
for u in p[(p.label == 0) & m].url.head(80):
    print("  ", u[:150])
