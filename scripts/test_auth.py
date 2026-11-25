import os, sys
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

# Test dev mode (no key)
os.environ.pop("ADMIN_API_KEY", None)
import importlib
import deployment.api.main as main
importlib.reload(main)
from fastapi.testclient import TestClient
c = TestClient(main.app)
r = c.post("/retraining/run", json={"trigger": "t", "min_samples": 30})
print("dev mode run:", r.status_code, r.json().get("status"))

# Test protected mode
os.environ["ADMIN_API_KEY"] = "secret123"
importlib.reload(main)
c2 = TestClient(main.app)
r = c2.post("/retraining/run", json={"trigger": "t", "min_samples": 30})
print("no key:", r.status_code)
r = c2.post("/retraining/run", json={"trigger": "t", "min_samples": 30}, headers={"X-Admin-API-Key": "wrong"})
print("wrong key:", r.status_code)
r = c2.post("/retraining/run", json={"trigger": "t", "min_samples": 30}, headers={"X-Admin-API-Key": "secret123"})
print("valid key:", r.status_code)
# public endpoint still open
r = c2.get("/health")
print("health:", r.status_code)
