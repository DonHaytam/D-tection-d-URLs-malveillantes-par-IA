import os, sys
os.environ["APP_ENV"] = "production"
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

# weak key
os.environ["ADMIN_API_KEY"] = "short"
os.environ["ALLOWED_ORIGINS"] = "http://localhost:8501"
import importlib, deployment.api.main as m
importlib.reload(m)
from fastapi.testclient import TestClient
try:
    with TestClient(m.app) as c:
        print("weak key: started (BAD)")
except Exception as e:
    print("weak key OK raised:", type(e).__name__, str(e)[:120])

# valid key
os.environ["ADMIN_API_KEY"] = "abcdefghijklmnopqrstuvwxyz012345"
importlib.reload(m)
try:
    with TestClient(m.app) as c:
        print("valid key: started OK, health:", c.get("/health").json()["admin_auth_enabled"])
except Exception as e:
    print("valid key FAILED:", type(e).__name__, str(e)[:120])
