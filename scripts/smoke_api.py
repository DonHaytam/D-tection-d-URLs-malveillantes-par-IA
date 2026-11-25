import json
import sys

import requests

BASE = "http://127.0.0.1:8000"


def show(label, data):
    print("\n==", label, "==")
    print(json.dumps(data, indent=2, ensure_ascii=False)[:2500])


# Find one client for each A/B variant
variants = {}
for i in range(30):
    cid = f"smoke-client-{i}"
    r = requests.post(f"{BASE}/predict", json={"url": "https://www.google.com/", "client_id": cid}, timeout=120)
    r.raise_for_status()
    data = r.json()
    variants.setdefault(data["variant"], (cid, data))
    if len(variants) == 2:
        break
print("variants found:", {k: v[0] for k, v in variants.items()})
for name, (cid, data) in variants.items():
    print(name, "->", data["model_version"], "score", round(data["score"], 4))

# Explanation + active learning flag on a suspicious URL
r = requests.post(f"{BASE}/predict", json={
    "url": "http://paypal-secure-login.verify-account.tk/login.php",
    "explain": True,
    "client_id": "smoke-client-explain",
}, timeout=120)
r.raise_for_status()
res = r.json()
print("\nphishing test:", res["verdict"], round(res["score"], 6), "variant", res["variant"],
      "active_learning", res["active_learning"], "prediction_id", res["prediction_id"])
exp = res.get("explanation") or {}
print("explain keys:", sorted(exp.keys()))
print("phishing signals:", exp.get("phishing_signals", [])[:5])
print("legit signals:", exp.get("legitimate_signals", [])[:5])
print("annotated segments:", (exp.get("annotated_url") or [])[:6])

# Feedback: incorrect with correction
r = requests.post(f"{BASE}/feedback", json={
    "prediction_id": res["prediction_id"],
    "feedback": "incorrect",
    "corrected_label": "legitimate",
    "comment": "smoke test correction",
}, timeout=60)
r.raise_for_status()
show("feedback", r.json()["stats"])

# Idempotent re-submission (latest wins)
r = requests.post(f"{BASE}/feedback", json={
    "prediction_id": res["prediction_id"],
    "feedback": "correct",
}, timeout=60)
r.raise_for_status()
show("feedback resubmit", r.json()["stats"])

# Active learning, stats, monitoring, ab, retraining
for path in ["/active-learning?limit=5", "/stats", "/monitoring?window_days=7",
             "/ab-test", "/retraining/status"]:
    r = requests.get(BASE + path, timeout=120)
    r.raise_for_status()
    data = r.json()
    print("\n==", path, "==")
    print(json.dumps(data, indent=2, ensure_ascii=False)[:1800])

# CSV export
r = requests.get(f"{BASE}/feedback/export", timeout=60)
r.raise_for_status()
print("\nCSV export first lines:\n", "\n".join(r.text.splitlines()[:4]))

# Retraining dry run (insufficient data path is safe and does not deploy)
r = requests.post(f"{BASE}/retraining/run", json={"trigger": "smoke", "min_samples": 30}, timeout=60)
r.raise_for_status()
print("\nretraining queued:", r.json())
