import sys
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")
import pandas as pd
import re

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
POOL = pd.read_csv(f"{ROOT}/data/integrated/external_pool.csv", usecols=["url", "label", "registrable_domain", "source"])
print("pool", len(POOL), POOL.label.value_counts().to_dict())

TOK = re.compile(r"login|signin|sign-in|sign_in|logon|auth|account|verify|verification|password|passwd|oauth|register|signup|sign-up|security|checkout|payment|billing|secure|session|sso|saml|openid|mfa|2fa", re.I)
BROAD = re.compile(r"login|signin|sign-in|sign_in|logon|auth|account|verify|verification|password|passwd|oauth|register|signup|sign-up|security|checkout|payment|billing|secure|session|sso|saml|openid|mfa|2fa|service", re.I)

for name, rx in [("TOK", TOK), ("BROAD", BROAD)]:
    m = POOL["url"].astype(str).str.contains(rx, regex=True)
    print(f"\n{name}: total={m.sum()} legit={((POOL.label==0)&m).sum()} phish={((POOL.label==1)&m).sum()}")
    sub = POOL[(POOL.label==0)&m]
    print("  legit unique domains:", sub.registrable_domain.nunique())
    print("  by source:", sub.source.value_counts().to_dict())
    print("  sample:")
    for u in sub.url.head(25):
        print("   ", u[:150])

# only path segment tokens (current definition-ish)
PATH_RE = re.compile(r"(?:^|/)(login|signin|sign-in|sign_in|logon|auth|account|accounts|verify|verification|password|passwd|oauth|register|signup|sign-up|security|checkout|payment|billing|wp-login\.php|login\.php|signin\.php|session|sso|saml|openid|mfa|2fa)(?:/|$|[.?])", re.I)
def path_of(u):
    try:
        rest = str(u).split("://",1)[1]
        return "/" + (rest.split("/",1)[1] if "/" in rest else "")
    except Exception:
        return ""
POOL["path"] = POOL["url"].map(path_of)
m = POOL["path"].str.contains(PATH_RE, regex=True)
print(f"\nPATH segment: total={m.sum()} legit={((POOL.label==0)&m).sum()} phish={((POOL.label==1)&m).sum()}")
print("  legit unique domains:", POOL[(POOL.label==0)&m].registrable_domain.nunique())
print("  by source:", POOL[(POOL.label==0)&m].source.value_counts().to_dict())
for u in POOL[(POOL.label==0)&m].url.head(40):
    print("   ", u[:150])
