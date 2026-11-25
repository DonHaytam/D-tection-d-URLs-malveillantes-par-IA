import sys
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")
from deployment.api.main import app
from fastapi.testclient import TestClient
c = TestClient(app)
print("health:", c.get("/health").json())
r = c.post("/predict", json={"url": "https://www.youtube.com/"})
d = r.json()
score_pct = round(d["score"] * 100, 2)
print("predict:", r.status_code, d["verdict"], str(score_pct) + " percent")