"""Feedback-driven retraining pipeline (safe, manual approval required).

The pipeline never deploys a model automatically.  It validates and dedupes
feedback-derived URLs, trains a candidate on TRAIN + confirmed feedback,
evaluates it on DEV, writes the candidate artifact, and leaves it in
``pending_approval`` state.
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time
from datetime import datetime, timezone

sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

import numpy as np
import pandas as pd

from src.data.validation import is_valid_url, normalize_url
from src.storage import db

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
FEEDBACK_DIR = os.path.join(ROOT, "data", "feedback")
CANDIDATES = os.path.join(ROOT, "models", "versions", "candidates")
CONFIG_PATH = os.path.join(ROOT, "configs", "retraining.json")
DEFAULT_MIN_SAMPLES = 30


def _load_config():
    default = {"enabled": True, "weekday": 0, "hour_utc": 2,
               "min_samples": DEFAULT_MIN_SAMPLES, "check_interval_s": 300}
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            default.update(json.load(f))
    except Exception:
        pass
    return default


def save_config(cfg):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def _infer_label(row):
    feedback = (row.get("user_feedback") or "").lower()
    verdict = (row.get("verdict") or "").upper()
    corrected = (row.get("corrected_label") or "").lower()
    if feedback == "correct":
        if verdict == "PHISHING":
            return 1
        if verdict == "LEGITIMATE":
            return 0
        return None
    if feedback == "incorrect":
        if corrected == "phishing":
            return 1
        if corrected == "legitimate":
            return 0
        if verdict == "PHISHING":
            return 0
        if verdict == "LEGITIMATE":
            return 1
        return None
    return None


def collect_feedback_dataset():
    rows = db.get_feedback_rows(limit=100000)
    records = []
    for row in rows:
        label = _infer_label(row)
        if label is None:
            continue
        url = str(row.get("url") or "").strip()
        if not is_valid_url(url):
            continue
        norm = normalize_url(url)
        if not norm:
            continue
        records.append({
            "url": url,
            "normalized_url": norm,
            "label": int(label),
            "prediction_id": row.get("id"),
            "feedback": row.get("user_feedback"),
        })
    df = pd.DataFrame(records)
    if df.empty:
        return df, {"feedback_rows": len(rows), "usable": 0, "duplicates": 0, "conflicts": 0}
    before = len(df)
    # Exact normalized duplicates with the same label collapse to one row.
    df = df.sort_values("prediction_id").drop_duplicates(subset=["normalized_url"], keep="last")
    duplicates = before - len(df)
    # Conflicting labels are quarantined, not guessed.
    conflict_mask = df.groupby("normalized_url")["label"].transform("nunique") > 1
    conflicts = int(conflict_mask.sum())
    df = df[~conflict_mask].reset_index(drop=True)
    meta = {"feedback_rows": len(rows), "usable": int(len(df)),
            "duplicates": int(duplicates), "conflicts": conflicts,
            "positive": int((df.label == 1).sum()) if len(df) else 0,
            "negative": int((df.label == 0).sum()) if len(df) else 0}
    return df, meta


def _metrics(y, scores):
    from sklearn.metrics import roc_curve
    from src.evaluation.metrics import compute_metrics

    m = compute_metrics(y, scores, threshold=0.5)
    fpr, tpr, thr = roc_curve(y, scores)
    ok = fpr <= 0.01
    m["recall_at_fpr_1pct"] = float(tpr[ok][int(np.argmax(tpr[ok]))]) if ok.any() else None
    m["threshold_at_fpr_1pct"] = float(thr[ok][int(np.argmax(tpr[ok]))]) if ok.any() else None
    pred3 = np.where(scores >= 0.75, 1, np.where(scores < 0.25, 0, 2))
    m["three_class_strict_recall"] = float((pred3[y == 1] == 1).mean())
    m["three_class_fpr"] = float((pred3[y == 0] == 1).mean())
    m["three_class_review_inclusive_recall"] = float((pred3[y == 1] >= 1).mean())
    return {k: (round(v, 6) if isinstance(v, float) else v) for k, v in m.items()}


def run_retraining(trigger="manual", min_samples=None, run_id=None):
    cfg = _load_config()
    min_samples = int(min_samples or cfg.get("min_samples", DEFAULT_MIN_SAMPLES))
    if run_id is None:
        run_id = db.create_retraining_run(trigger=trigger, notes="Pipeline demarre.")
    else:
        db.update_retraining_run(run_id, status="running", notes="Pipeline demarre.")
    try:
        df, meta = collect_feedback_dataset()
        os.makedirs(FEEDBACK_DIR, exist_ok=True)
        out_csv = os.path.join(FEEDBACK_DIR, f"feedback_{run_id}.csv")
        if not df.empty:
            df[["url", "label", "prediction_id", "feedback"]].to_csv(out_csv, index=False)
        db.update_retraining_run(run_id, n_feedback=meta.get("usable", 0),
                                 n_positive=meta.get("positive", 0),
                                 n_negative=meta.get("negative", 0),
                                 notes=json.dumps(meta, ensure_ascii=False))
        if len(df) < min_samples:
            db.update_retraining_run(run_id, status="insufficient_data",
                                     finished_at=db.now_iso(),
                                     notes=json.dumps({**meta, "min_samples": min_samples},
                                                      ensure_ascii=False))
            return run_id

        import joblib
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression

        train = pd.read_csv(os.path.join(ROOT, "data/splits/TRAIN.csv"), usecols=["url", "label"])
        dev = pd.read_csv(os.path.join(ROOT, "data/splits/DEV.csv"), usecols=["url", "label"])
        train = pd.concat([train, df[["url", "label"]]], ignore_index=True)
        train = train.drop_duplicates(subset=["url"], keep="last").reset_index(drop=True)
        y_train = train["label"].astype(int).values
        y_dev = dev["label"].astype(int).values
        vec = TfidfVectorizer(analyzer="char", ngram_range=(3, 5), min_df=3,
                              max_features=20000, lowercase=True, sublinear_tf=True)
        Xtr = vec.fit_transform(train["url"].astype(str).tolist())
        Xdev = vec.transform(dev["url"].astype(str).tolist())
        model = LogisticRegression(C=1.0, class_weight="balanced", solver="lbfgs",
                                   max_iter=300, tol=1e-3, random_state=42, n_jobs=1)
        model.fit(Xtr, y_train)
        scores = model.predict_proba(Xdev)[:, 1]
        metrics = _metrics(y_dev, scores)
        os.makedirs(CANDIDATES, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        artifact = os.path.join(CANDIDATES, f"RETRAIN_{stamp}_run{run_id}.joblib")
        joblib.dump({"model": model, "vectorizer": vec, "kind": "char_tfidf",
                     "feature_names": None, "scaler": None, "numeric_feature_names": None},
                    artifact)
        db.update_retraining_run(run_id, status="pending_approval", n_train=int(len(train)),
                                 metrics_json=json.dumps(metrics, ensure_ascii=False),
                                 artifact_path=artifact, finished_at=db.now_iso(),
                                 notes=json.dumps({**meta, "min_samples": min_samples},
                                                  ensure_ascii=False))
    except Exception as exc:
        db.update_retraining_run(run_id, status="failed", finished_at=db.now_iso(),
                                 notes=f"{type(exc).__name__}: {exc}")
    return run_id


def approve(run_id, approved=True, notes=None):
    run = next((r for r in db.get_retraining_runs(limit=100) if int(r["id"]) == int(run_id)), None)
    if run is None:
        raise KeyError("run not found")
    db.update_retraining_run(run_id, approved=1 if approved else 0,
                             approved_at=db.now_iso(),
                             status="approved" if approved else "rejected",
                             notes=notes if notes is not None else run.get("notes"))
    return run_id


def _is_due(cfg):
    last = db.get_last_retraining_run()
    now = datetime.now(timezone.utc)
    if last is None:
        return now.weekday() == int(cfg.get("weekday", 0)) and now.hour >= int(cfg.get("hour_utc", 2))
    try:
        last_dt = datetime.fromisoformat(str(last["created_at"]).replace("Z", "+00:00"))
    except Exception:
        return True
    if last_dt.tzinfo is None:
        last_dt = last_dt.replace(tzinfo=timezone.utc)
    return (now - last_dt).total_seconds() >= 7 * 24 * 3600


def scheduler_tick():
    cfg = _load_config()
    if not cfg.get("enabled", True):
        return None
    if not _is_due(cfg):
        return None
    summary = db.feedback_summary()
    if summary["with_feedback"] < int(cfg.get("min_samples", DEFAULT_MIN_SAMPLES)):
        return None
    return run_retraining(trigger="scheduler", min_samples=cfg.get("min_samples"))


def start_scheduler():
    def loop():
        while True:
            try:
                scheduler_tick()
            except Exception:
                pass
            time.sleep(int(_load_config().get("check_interval_s", 300)))
    t = threading.Thread(target=loop, name="retraining-scheduler", daemon=True)
    t.start()
    return t
