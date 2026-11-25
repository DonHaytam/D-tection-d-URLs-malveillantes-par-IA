import os, sys
os.environ["APP_ENV"] = "production"
os.environ["ADMIN_API_KEY"] = "abcdefghijklmnopqrstuvwxyz012345"
os.environ["ALLOWED_ORIGINS"] = "*"
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")
import importlib, deployment.api.main as m
importlib.reload(m)
from fastapi.testclient import TestClient
try:
    with TestClient(m.app) as c:
        print("wildcard CORS: started (BAD)")
except Exception as e:
    print("wildcard CORS OK raised:", type(e).__name__, str(e)[:120])

# missing origins
os.environ["ALLOWED_ORIGINS"] = ""
importlib.reload(m)
try:
    with TestClient(m.app) as c:
        print("empty origins: started (BAD)")
except Exception as e:
    print("empty origins OK raised:", type(e).__name__, str(e)[:120])
