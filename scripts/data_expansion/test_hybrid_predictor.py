import sys
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")
from src.inference.predictor import Predictor

p = Predictor(
    "D:/openhands/projects/v2/phishing_ai_master/models/versions/M1_HYBRID_REP_V2.joblib",
    "D:/openhands/projects/v2/phishing_ai_master/models/versions/metadata.json",
)
urls = [
    "https://www.paypal.com/signin",
    "https://github.com/login",
    "https://accounts.google.com/signin",
    "https://www.amazon.com/ap/signin",
    "https://login.microsoftonline.com/",
    "https://www.linkedin.com/login",
    "https://www.dropbox.com/login",
    "https://www.apple.com/shop/account/home",
]
for u in urls:
    r = p.predict_one(u)
    print(f"{r['score']*100:6.2f}% {r['verdict']:10s} {u}")
print("kind:", p.kind, "tranco:", len(p.tranco_rank), "thresholds:", p.low, p.high)

from src.inference.explainability import get_top_contributing_features
import joblib
art = joblib.load("D:/openhands/projects/v2/phishing_ai_master/models/versions/M1_HYBRID_REP_V2.joblib")
print(get_top_contributing_features("https://www.paypal.com/signin", art, top_n=5))
