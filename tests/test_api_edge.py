"""API edge-case tests (run against the live app via TestClient)."""
import sys, os
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

from fastapi.testclient import TestClient
import deployment.api.main as main

client = TestClient(main.app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    d = r.json()
    assert d["model_loaded"] is True
    assert d["model_version"] == "M1_LR_HARDNEG"
    assert d["ensemble_loaded"] is True


def test_predict_empty_url():
    r = client.post("/predict", json={"url": "   "})
    assert r.status_code == 400


def test_predict_missing_url():
    r = client.post("/predict", json={})
    assert r.status_code == 422


def test_predict_batch_empty():
    r = client.post("/predict_batch", json={"urls": []})
    assert r.status_code == 400


def test_predict_batch_over_limit():
    r = client.post("/predict_batch", json={"urls": ["https://example.com"] * 201})
    assert r.status_code == 400


def test_predict_batch_ok():
    r = client.post("/predict_batch", json={"urls": ["https://www.google.com/", "http://evil.tk/login"]})
    assert r.status_code == 200
    d = r.json()
    assert len(d["results"]) == 2
    for res in d["results"]:
        assert 0.0 <= res["score"] <= 1.0
        assert res["verdict"] in ("PHISHING", "LEGITIMATE", "NEEDS_REVIEW")


def test_feedback_invalid_label():
    # create a prediction first
    r = client.post("/predict", json={"url": "https://example.com"})
    pid = r.json()["prediction_id"]
    r2 = client.post("/feedback", json={"prediction_id": pid, "feedback": "bogus"})
    assert r2.status_code == 400


def test_feedback_not_found():
    r = client.post("/feedback", json={"prediction_id": 999999, "feedback": "correct"})
    assert r.status_code == 404


def test_active_learning_range():
    r = client.get("/active-learning?limit=5&low=0.4&high=0.6")
    assert r.status_code == 200
    d = r.json()
    assert d["low"] == 0.4 and d["high"] == 0.6
    for item in d["items"]:
        assert 0.4 <= item["score"] <= 0.6


def test_monitoring_no_crash():
    r = client.get("/monitoring?window_days=7")
    assert r.status_code == 200
    d = r.json()
    assert "alerts" in d
    assert "psi" in d or d["psi"] is None


def test_ab_test():
    r = client.get("/ab-test")
    assert r.status_code == 200
    d = r.json()
    assert "variants" in d
    assert "winner" in d


def test_three_class_policy():
    # verify decision policy mapping via a known low score url
    r = client.post("/predict", json={"url": "https://www.google.com/"})
    d = r.json()
    assert 0.0 <= d["score"] <= 1.0
    if d["score"] < 0.25:
        assert d["verdict"] == "LEGITIMATE"
    elif d["score"] >= 0.75:
        assert d["verdict"] == "PHISHING"
    else:
        assert d["verdict"] == "NEEDS_REVIEW"


def test_ab_stable_assignment():
    cid = "stable-client-abc"
    r1 = client.post("/predict", json={"url": "https://www.google.com/", "client_id": cid})
    r2 = client.post("/predict", json={"url": "https://www.example.com/", "client_id": cid})
    assert r1.json()["variant"] == r2.json()["variant"]


def test_cors_allowed_origin():
    r = client.get("/health", headers={"Origin": "http://localhost:8501"})
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") in ("http://localhost:8501", "*")


def test_cors_preflight():
    r = client.options("/predict", headers={
        "Origin": "http://localhost:8501",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    })
    assert r.status_code in (200, 204)


def test_cors_rejected_origin_not_credentialed():
    # A non-allowlisted origin must not receive allow-credentials true
    r = client.get("/health", headers={"Origin": "http://evil.example"})
    # Either no allow-origin header or not the evil origin
    acao = r.headers.get("access-control-allow-origin")
    assert acao != "http://evil.example" or acao is None
