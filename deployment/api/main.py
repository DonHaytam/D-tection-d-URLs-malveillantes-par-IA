"""FastAPI backend for phishing URL detection, feedback and operations."""
import csv
import hashlib
import hmac
import io
import os
import sys
import threading
import time
import uuid

sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

# Optional .env support (env vars take precedence)
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join("D:/openhands/projects/v2/phishing_ai_master", ".env"))
except Exception:
    pass

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional

from src.storage import db

# --- CORS allowlist (no wildcard unless explicitly requested) ---
_DEFAULT_ORIGINS = "http://localhost:8501,http://127.0.0.1:8501,http://localhost:8000,http://127.0.0.1:8000"
ALLOWED_ORIGINS = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", _DEFAULT_ORIGINS).split(",") if o.strip()]
ALLOW_CREDENTIALS = "*" not in ALLOWED_ORIGINS

APP_ENV = os.environ.get("APP_ENV", "development").lower()
if APP_ENV not in ("development", "testing", "production"):
    APP_ENV = "development"

ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY")

# Minimum acceptable length for an admin key (when configured)
MIN_ADMIN_KEY_LENGTH = 24


def _is_weak_key(key: str) -> bool:
    if not key or len(key) < MIN_ADMIN_KEY_LENGTH:
        return True
    # reject trivially repeated/low-entropy keys
    if len(set(key)) < 8:
        return True
    return False


def validate_production_config():
    """Raise RuntimeError if production config is invalid. Called at startup."""
    if APP_ENV != "production":
        return
    if not ADMIN_API_KEY:
        raise RuntimeError("APP_ENV=production requires ADMIN_API_KEY to be set")
    if _is_weak_key(ADMIN_API_KEY):
        raise RuntimeError("ADMIN_API_KEY is too weak (min %d chars, sufficient entropy)" % MIN_ADMIN_KEY_LENGTH)
    if not ALLOWED_ORIGINS or "*" in ALLOWED_ORIGINS:
        raise RuntimeError("APP_ENV=production requires explicit ALLOWED_ORIGINS (no wildcard)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup validation (production only)
    validate_production_config()
    if APP_ENV == "development" and not ADMIN_API_KEY:
        import warnings
        warnings.warn("ADMIN_API_KEY not set: administrative endpoints are UNPROTECTED (dev mode)", stacklevel=2)
    db.init_db()
    try:
        from src.retraining.pipeline import start_scheduler
        start_scheduler()
    except Exception:
        pass
    yield
    # Shutdown: nothing persistent to close


app = FastAPI(title="Phishing AI Master 2", version="0.3.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Admin-API-Key", "Authorization"],
)


def require_admin(x_admin_api_key: Optional[str] = Header(default=None, alias="X-Admin-API-Key")):
    """Protect administrative endpoints with a constant-time API key check.

    If ADMIN_API_KEY is unset, endpoints run in dev mode (open). Set the env var
    in production to enforce authentication.
    """
    if not ADMIN_API_KEY:
        if APP_ENV == "production":
            raise HTTPException(status_code=503, detail="Admin authentication not configured")
        return True
    if not x_admin_api_key or not hmac.compare_digest(x_admin_api_key, ADMIN_API_KEY):
        raise HTTPException(status_code=401, detail="Invalid or missing admin API key")
    return True


# --- Minimal RBAC (permission constants; enforcement via admin key) ---
PERM_ADMIN = "admin"
PERM_ANALYST = "analyst"
PERM_VIEWER = "viewer"

ROLE_PERMISSIONS = {
    PERM_ADMIN: {"retrain", "approve", "schedule", "read_monitoring", "read_history", "read_stats"},
    PERM_ANALYST: {"read_monitoring", "read_history", "read_stats"},
    PERM_VIEWER: {"read_history", "read_stats"},
}


def require_permission(permission: str):
    def _dep(x_admin_api_key: Optional[str] = Header(default=None, alias="X-Admin-API-Key")):
        if not ADMIN_API_KEY:
            if APP_ENV == "production":
                raise HTTPException(status_code=503, detail="Admin authentication not configured")
            return PERM_ADMIN
        if not x_admin_api_key or not hmac.compare_digest(x_admin_api_key, ADMIN_API_KEY):
            raise HTTPException(status_code=401, detail="Invalid or missing admin API key")
        if permission not in ROLE_PERMISSIONS[PERM_ADMIN]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return PERM_ADMIN
    return _dep


MODEL_PATH = os.environ.get("MODEL_PATH", "D:/openhands/projects/v2/phishing_ai_master/models/versions/M1_LR_HARDNEG.joblib")
META_PATH = os.environ.get("META_PATH", "D:/openhands/projects/v2/phishing_ai_master/models/versions/metadata.json")
AB_TEST_ENABLED = os.environ.get("AB_TEST_ENABLED", "1") == "1"
AB_TEST_SPLIT = float(os.environ.get("AB_TEST_SPLIT", "0.5"))
LOW, HIGH = 0.4, 0.6

_predictor = None
_ensemble = None
_m1_artifact = None


def get_predictor():
    global _predictor
    if _predictor is None:
        if os.path.exists(MODEL_PATH):
            from src.inference.predictor import Predictor
            _predictor = Predictor(MODEL_PATH, META_PATH)
        else:
            return None
    return _predictor


def get_ensemble():
    global _ensemble
    if _ensemble is None:
        base = get_predictor()
        if base is None:
            return None
        from src.inference.ensemble import EnsemblePredictor
        _ensemble = EnsemblePredictor(base)
    return _ensemble


def get_m1_artifact():
    global _m1_artifact
    if _m1_artifact is None:
        import joblib
        _m1_artifact = joblib.load(MODEL_PATH)
    return _m1_artifact


def assign_variant(client_id):
    if not AB_TEST_ENABLED:
        return "M1"
    digest = hashlib.sha256(str(client_id).encode("utf-8")).hexdigest()[:8]
    value = int(digest, 16) / 0xFFFFFFFF
    return "ENSEMBLE" if value < AB_TEST_SPLIT else "M1"


class PredictRequest(BaseModel):
    url: str
    client_id: Optional[str] = None


class BatchRequest(BaseModel):
    urls: List[str]
    client_id: Optional[str] = None


class FeedbackRequest(BaseModel):
    prediction_id: int
    feedback: str
    corrected_label: Optional[str] = None
    comment: Optional[str] = None


class RetrainRequest(BaseModel):
    trigger: str = "manual"
    min_samples: int = 30


class ApproveRequest(BaseModel):
    run_id: int
    approved: bool = True
    notes: Optional[str] = None


class ScheduleRequest(BaseModel):
    enabled: Optional[bool] = None
    weekday: Optional[int] = None
    hour_utc: Optional[int] = None
    min_samples: Optional[int] = None


def _predict(url, client_id):
    p = get_predictor()
    if p is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    variant = assign_variant(client_id)
    if variant == "ENSEMBLE":
        ens = get_ensemble()
        if ens is None or not ens.available:
            result = p.predict_one(url)
            variant = "M1"
        else:
            result = ens.predict_one(url)
    else:
        result = p.predict_one(url)
    result["variant"] = variant
    result["client_id"] = client_id
    result["active_learning"] = bool(LOW <= result["score"] <= HIGH)
    rid, ts = db.save_prediction(url, result, explanation=None,
                                 variant=variant, client_id=client_id)
    result["prediction_id"] = rid
    result["timestamp"] = ts
    return result


@app.get("/health")
def health():
    p = get_predictor()
    ens = get_ensemble()
    return {"status": "ok", "model_loaded": p is not None,
            "model_version": (p.version if p else None),
            "app_env": APP_ENV,
            "ab_test_enabled": AB_TEST_ENABLED,
            "ensemble_loaded": bool(ens and ens.available),
            "allowed_origins": ALLOWED_ORIGINS,
            "admin_auth_enabled": bool(ADMIN_API_KEY),
            "database": db.db_path()}


@app.post("/predict")
def predict(req: PredictRequest):
    if not str(req.url or "").strip():
        raise HTTPException(status_code=400, detail="URL vide")
    client_id = req.client_id or uuid.uuid4().hex
    return _predict(req.url, client_id)


@app.post("/predict_batch")
def predict_batch(req: BatchRequest):
    if not req.urls:
        raise HTTPException(status_code=400, detail="Liste d'URL vide")
    if len(req.urls) > 200:
        raise HTTPException(status_code=400, detail="Maximum 200 URLs par lot")
    client_id = req.client_id or uuid.uuid4().hex
    results = []
    for url in req.urls:
        try:
            results.append(_predict(url, client_id))
        except HTTPException:
            raise
        except Exception as exc:
            results.append({"url": url, "verdict": "ERROR", "score": 0.0,
                            "model_version": "N/A", "thresholds": {"low": 0.25, "high": 0.75},
                            "processing_time_ms": 0, "error": str(exc)})
    return {"results": results, "variant": assign_variant(client_id), "client_id": client_id}


@app.post("/feedback")
def feedback(req: FeedbackRequest):
    try:
        stats = db.set_feedback(req.prediction_id, req.feedback, req.corrected_label, req.comment)
    except KeyError:
        raise HTTPException(status_code=404, detail="Prediction introuvable")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"ok": True, "feedback": req.feedback, "stats": stats,
            "active_learning": db.get_active_learning(limit=10)}


@app.get("/history")
def history(limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0)):
    return {"items": db.get_history(limit=limit, offset=offset)}


@app.get("/stats")
def stats():
    return db.get_stats()


@app.get("/active-learning")
def active_learning(limit: int = Query(50, ge=1, le=500),
                    low: float = Query(LOW, ge=0.0, le=1.0),
                    high: float = Query(HIGH, ge=0.0, le=1.0)):
    return db.get_active_learning(limit=limit, low=low, high=high)


@app.get("/monitoring")
def monitoring(window_days: int = Query(7, ge=1, le=90)):
    return db.get_monitoring(window_days=window_days)


@app.get("/ab-test")
def ab_test():
    return db.get_ab_test()


@app.get("/feedback/export")
def feedback_export():
    rows = db.get_feedback_rows(limit=100000)
    buf = io.StringIO()
    fields = ["id", "url", "verdict", "score", "model_version", "variant", "timestamp",
              "user_feedback", "corrected_label", "feedback_comment", "feedback_timestamp"]
    writer = csv.DictWriter(buf, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row.get(k) for k in fields})
    buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=feedback_data.csv"})


@app.get("/retraining/status")
def retraining_status():
    from src.retraining.pipeline import _load_config
    return {"runs": db.get_retraining_runs(limit=20), "schedule": _load_config(),
            "feedback": db.feedback_summary()}


@app.post("/retraining/run")
def retraining_run(req: RetrainRequest, _admin=Depends(require_admin)):
    from src.retraining.pipeline import run_retraining
    run_id = db.create_retraining_run(trigger=req.trigger, notes="Job en file d'attente.")

    def job():
        try:
            run_retraining(trigger=req.trigger, min_samples=req.min_samples, run_id=run_id)
        except Exception as exc:
            db.update_retraining_run(run_id, status="failed", finished_at=db.now_iso(),
                                     notes=f"{type(exc).__name__}: {exc}")
    threading.Thread(target=job, name="manual-retraining", daemon=True).start()
    return {"ok": True, "run_id": run_id, "status": "queued"}


@app.post("/retraining/approve")
def retraining_approve(req: ApproveRequest, _admin=Depends(require_admin)):
    from src.retraining.pipeline import approve
    try:
        approve(req.run_id, approved=req.approved, notes=req.notes)
    except KeyError:
        raise HTTPException(status_code=404, detail="Run introuvable")
    return {"ok": True, "run_id": req.run_id, "approved": req.approved}


@app.get("/retraining/schedule")
def retraining_schedule_get():
    from src.retraining.pipeline import _load_config
    return _load_config()


@app.post("/retraining/schedule")
def retraining_schedule_set(req: ScheduleRequest, _admin=Depends(require_admin)):
    from src.retraining.pipeline import _load_config, save_config
    cfg = _load_config()
    for key in ("enabled", "weekday", "hour_utc", "min_samples"):
        value = getattr(req, key)
        if value is not None:
            cfg[key] = value
    save_config(cfg)
    return cfg


@app.get("/ensemble")
def ensemble_info():
    ens = get_ensemble()
    return {"models": ["M1_LR_HARDNEG", "M2_SVM", "M5_XGBOOST"],
            "method": "weighted_soft_voting",
            "weights": {"M1": 0.5, "M2": 0.3, "M5": 0.2},
            "available": bool(ens and ens.available),
            "metrics": {"recall": 0.8595, "fpr": 0.0345, "roc_auc": 0.9714}}