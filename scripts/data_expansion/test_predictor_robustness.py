import sys
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")
from src.inference.predictor import Predictor

cases = [
    "https://www.paypal.com/signin",
    "http://example.com",
    "example.com",
    "",
    "   ",
    "not a url",
    "http://",
    "https://",
    "ftp://example.com/file",
    "https://example.com:99999/",
    "https://exa mple.com/",
    "https://" + "a" * 300 + ".com/",
    "https://example.com/" + "a" * 3000,
    "https://xn--bcher-kva.example/",
    "https://user:pass@example.com/login",
    "javascript:alert(1)",
    "data:text/html,<script>alert(1)</script>",
    "//example.com/login",
    "https://example.com/login?next=https://evil.com",
]
for label, path in [
    ("hybrid", "D:/openhands/projects/v2/phishing_ai_master/models/versions/M1_HYBRID_REP_V2.joblib"),
    ("baseline", "D:/openhands/projects/v2/phishing_ai_master/models/versions/M1_LR_HARDNEG.joblib"),
]:
    print("===", label)
    p = Predictor(path, "D:/openhands/projects/v2/phishing_ai_master/models/versions/metadata.json")
    for u in cases:
        try:
            r = p.predict_one(u)
            print(f"  ok {r['score']*100:7.2f}% {r['verdict']:12s} {u[:80]!r}")
        except Exception as e:
            print(f"  ERR {type(e).__name__}: {e} :: {u[:80]!r}")
