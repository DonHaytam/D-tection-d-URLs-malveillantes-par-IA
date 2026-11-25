import os
import urllib.request

BASE = "D:/openhands/projects/SI project"
RAW_DIR = os.path.join(BASE, "data", "raw")
DEST = os.path.join(RAW_DIR, "phiusiil_phishing_url_dataset.zip")

URL = "https://archive.ics.uci.edu/static/public/967/phiusiil+phishing+url+dataset.zip"

os.makedirs(RAW_DIR, exist_ok=True)

print("Downloading", URL)
req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=180) as r, open(DEST, "wb") as f:
    f.write(r.read())

print("Saved to", DEST, os.path.getsize(DEST), "bytes")
