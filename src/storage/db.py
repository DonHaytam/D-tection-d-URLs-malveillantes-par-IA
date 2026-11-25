"""SQLite persistence for predictions, feedback, monitoring and retraining.

The database is deliberately simple: one prediction row per analysed URL,
one feedback row per prediction (latest feedback wins), plus retraining and
monitoring audit tables.  No URL is ever fetched or resolved.
"""

from __future__ import annotations

import json
import math
import os
import sqlite3
from datetime import datetime, timedelta, timezone

import sys
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

from src.data.provenance import registrable_domain
from src.data.validation import normalize_url
from src.storage.drift_fixes import _compute_domain_drift

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
DEFAULT_DB_PATH = os.path.join(ROOT, "database", "predictions.db")
DEFAULT_DB_PATH = os.environ.get("DB_PATH", DEFAULT_DB_PATH)

FEEDBACK_VALUES = {"correct", "incorrect", "unknown"}
CORRECTED_LABELS = {"phishing", "legitimate", None}
UNCERTAIN_LOW = 0.4
UNCERTAIN_HIGH = 0.6
ALERT_INCORRECT_RATE = 0.05
MIN_FEEDBACK_FOR_ALERT = 20
MIN_AL_QUEUE = 3

#: Path to the database file (exported for API access)
def db_path():
    """Return the path to the database file."""
    return DEFAULT_DB_PATH


def init_db():
    """Initialise la base de données si nécessaire."""
    db_path_val = DEFAULT_DB_PATH
    os.makedirs(os.path.dirname(db_path_val), exist_ok=True)
    conn = sqlite3.connect(db_path_val)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            verdict TEXT NOT NULL,
            score REAL NOT NULL,
            user_feedback TEXT,
            variant TEXT,
            model_version TEXT,
            timestamp TEXT NOT NULL,
            registrable_domain TEXT
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prediction_id INTEGER,
            user_feedback TEXT,
            timestamp TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (prediction_id) REFERENCES predictions(id)
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS retraining_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_type TEXT,
            eligible INTEGER,
            total INTEGER,
            positive INTEGER,
            negative INTEGER,
            details_json TEXT,
            timestamp TEXT NOT NULL
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS monitoring_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            severity TEXT,
            message TEXT,
            timestamp TEXT DEFAULT (datetime('now'))
        )"""
    )
    conn.commit()
    conn.close()


def connect():
    """Retourne une connexion SQLite vers la base par défaut."""
    db_path_val = DEFAULT_DB_PATH
    if not os.path.exists(db_path_val):
        init_db()
    conn = sqlite3.connect(db_path_val, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def feedback_summary():
    """Return global feedback statistics with sample sizes."""
    init_db()
    conn = connect()
    total = conn.execute("SELECT COUNT(*) AS n FROM predictions").fetchone()["n"]
    row = conn.execute(
        """SELECT
             SUM(CASE WHEN user_feedback IS NOT NULL THEN 1 ELSE 0 END) AS with_fb,
             SUM(CASE WHEN user_feedback='correct' THEN 1 ELSE 0 END) AS correct,
             SUM(CASE WHEN user_feedback='incorrect' THEN 1 ELSE 0 END) AS incorrect,
             SUM(CASE WHEN user_feedback='unknown' THEN 1 ELSE 0 END) AS unknown
           FROM predictions"""
    ).fetchone()
    conn.close()
    with_fb = int(row["with_fb"] or 0)
    correct = int(row["correct"] or 0)
    incorrect = int(row["incorrect"] or 0)
    unknown = int(row["unknown"] or 0)
    rate = (incorrect / with_fb) if with_fb else 0.0
    if with_fb:
        if with_fb == 1:
            sample_note = f"on {with_fb} feedback"
        else:
            sample_note = f"on {with_fb} feedbacks"
    else:
        sample_note = "aucun retour"
    return {
        "total": int(total),
        "with_feedback": with_fb,
        "correct": correct,
        "incorrect": incorrect,
        "unknown": unknown,
        "incorrect_rate": round(rate, 6),
        "alert_threshold": ALERT_INCORRECT_RATE,
        "alert": bool(with_fb >= MIN_FEEDBACK_FOR_ALERT and rate > ALERT_INCORRECT_RATE),
        "alert_ready": bool(with_fb >= MIN_FEEDBACK_FOR_ALERT),
        "sample_note": sample_note,
    }


def _agg(rows):
    """Aggregate stats for a list of prediction rows."""
    n = len(rows)
    if n == 0:
        return {
            "n": 0,
            "feedback": 0,
            "correct": 0,
            "incorrect": 0,
            "unknown": 0,
            "incorrect_rate": 0.0,
            "avg_score": None,
            "sample_note": "échantillon vide",
        }
    fb = [r for r in rows if r["user_feedback"]]
    incorrect = sum(1 for r in fb if r["user_feedback"] == "incorrect")
    correct = sum(1 for r in fb if r["user_feedback"] == "correct")
    unknown = sum(1 for r in fb if r["user_feedback"] == "unknown")
    scores = [float(r["score"]) for r in rows if r["score"] is not None]
    if fb:
        incorrect_rate = round(incorrect / len(fb), 6)
        avg_score = round(sum(scores) / len(scores), 6) if scores else None
        if len(fb) == 1:
            sample_note = f"sur {len(fb)} feedback"
        else:
            sample_note = f"sur {len(fb)} feedbacks"
    else:
        incorrect_rate = 0.0
        avg_score = None
        sample_note = "aucun retour"
    return {
        "n": n,
        "feedback": len(fb),
        "correct": correct,
        "incorrect": incorrect,
        "unknown": unknown,
        "incorrect_rate": incorrect_rate,
        "avg_score": avg_score,
        "sample_note": sample_note,
    }


def save_prediction(url, result, explanation=None, variant=None, client_id=None):
    """Save a prediction to the database.

    Returns (id, timestamp) of the inserted row.
    """
    init_db()
    conn = connect()
    # Normalize URL and get registrable domain
    norm = normalize_url(url)
    domain = registrable_domain(url)

    # Determine verdict from score
    score = float(result["score"])
    verdict = result.get("verdict", "NEEDS_REVIEW")

    # Determine model_version from variant
    if variant and variant.upper() == "ENSEMBLE":
        model_version = "ENSEMBLE"
    else:
        model_version = "M1"

    ts = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """INSERT INTO predictions
           (url, verdict, score, user_feedback, variant, model_version, timestamp, registrable_domain)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (url, verdict, score, None, variant, model_version, ts, domain),
    )
    pred_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()
    return (pred_id, ts)


def set_feedback(prediction_id, feedback, corrected_label=None, comment=None):
    """Set feedback for a prediction.

    Implements latest-feedback-wins rule.
    Returns the number of rows updated.
    Raises KeyError if the prediction does not exist.
    """
    init_db()
    conn = connect()
    # Validate feedback value
    if feedback not in FEEDBACK_VALUES:
        raise ValueError(f"Invalid feedback label: {feedback!r}. Must be one of {FEEDBACK_VALUES}")
    # Check that the prediction exists
    pred = conn.execute("SELECT id FROM predictions WHERE id = ?", (prediction_id,)).fetchone()
    if pred is None:
        raise KeyError(f"Prediction {prediction_id} not found")
    # Latest feedback wins: delete any existing feedback for this prediction,
    # then insert the new one (since feedback table has no UNIQUE constraint on prediction_id)
    conn.execute("DELETE FROM feedback WHERE prediction_id = ?", (prediction_id,))
    ts = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """INSERT INTO feedback (prediction_id, user_feedback, timestamp)
           VALUES (?, ?, ?)""",
        (prediction_id, feedback, ts),
    )
    # Also update the prediction's user_feedback field
    conn.execute(
        """UPDATE predictions SET user_feedback = ? WHERE id = ?""",
        (feedback, prediction_id),
    )
    conn.commit()
    conn.close()
    return 1


def get_stats():
    """Return basic statistics about predictions."""
    init_db()
    conn = connect()
    total = conn.execute("SELECT COUNT(*) AS n FROM predictions").fetchone()["n"]
    with_fb = conn.execute(
        "SELECT COUNT(*) AS n FROM predictions WHERE user_feedback IS NOT NULL"
    ).fetchone()["n"]
    correct = conn.execute(
        "SELECT COUNT(*) AS n FROM predictions WHERE user_feedback='correct'"
    ).fetchone()["n"]
    incorrect = conn.execute(
        "SELECT COUNT(*) AS n FROM predictions WHERE user_feedback='incorrect'"
    ).fetchone()["n"]
    conn.close()
    return {
        "total": int(total),
        "with_feedback": int(with_fb),
        "correct": int(correct),
        "incorrect": int(incorrect),
        "incorrect_rate": round(incorrect / with_fb, 6) if with_fb else 0.0,
    }


def get_feedback_rows(limit=100000):
    """Return all feedback rows with associated prediction data."""
    init_db()
    conn = connect()
    rows = conn.execute(
        """SELECT p.id, p.url, p.verdict, p.score, p.user_feedback,
          p.variant, p.model_version, p.timestamp, r.feedback, r.user_feedback, r.timestamp
           FROM predictions p
           LEFT JOIN (SELECT prediction_id, user_feedback, timestamp,
                      FROM feedback
                      WHERE rowid IN (SELECT MAX(rowid) FROM feedback GROUP BY prediction_id)) r
           ON p.id = r.prediction_id
           ORDER BY p.id DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_ab_test():
    """Return A/B test results with minimum sample-size policy."""
    init_db()
    conn = connect()
    rows = [dict(r) for r in conn.execute(
        """SELECT id, verdict, score, user_feedback, variant, model_version, timestamp
           FROM predictions ORDER BY id DESC"""
    ).fetchall()]
    conn.close()
    groups = {}
    for r in rows:
        variant = r["variant"] or ("ENSEMBLE" if "ENSEMBLE" in str(r["model_version"]).upper() else "M1")
        groups.setdefault(variant, []).append(r)
    out = {}
    for variant, items in groups.items():
        a = _agg(items)
        verdicts = {}
        for r in items:
            v = r["verdict"] or "UNKNOWN"
            verdicts[v] = verdicts.get(v, 0) + 1
        a["verdicts"] = verdicts
        out[variant] = a
    winner = "insufficient_data"
    # Minimum sample policy: both variants must have at least MIN_FEEDBACK_FOR_ALERT feedback
    if "M1" in out and "ENSEMBLE" in out:
        if out["M1"]["feedback"] >= MIN_FEEDBACK_FOR_ALERT and out["ENSEMBLE"]["feedback"] >= MIN_FEEDBACK_FOR_ALERT:
            if out["ENSEMBLE"]["incorrect_rate"] < out["M1"]["incorrect_rate"]:
                winner = "ENSEMBLE"
            elif out["ENSEMBLE"]["incorrect_rate"] > out["M1"]["incorrect_rate"]:
                winner = "M1"
            else:
                winner = "tie"
    return {
        "variants": out,
        "winner": winner,
        "ensemble_weights": {"M1": 0.5, "M2": 0.3, "M5": 0.2},
        "offline_reference": {"recall": 0.8595, "fpr": 0.0345, "roc_auc": 0.9714,
                              "note": "DEV, weighted soft voting 0.5/0.3/0.2"},
    }


def create_retraining_run(trigger=None, run_type=None, notes=None, details=None, **kwargs):
    """Create a retraining run record.

    Returns the run id.
    """
    init_db()
    conn = connect()
    rt = trigger or run_type or "manual"
    eligible = int((details or {}).get("eligible", 0) if details else kwargs.get("eligible", 0))
    total = int((details or {}).get("total", 0) if details else kwargs.get("total", 0))
    positive = int((details or {}).get("positive", 0) if details else kwargs.get("positive", 0))
    negative = int((details or {}).get("negative", 0) if details else kwargs.get("negative", 0))
    details_json = json.dumps(details) if details else json.dumps(kwargs) if kwargs else (notes if notes else None)
    ts = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """INSERT INTO retraining_runs
           (run_type, eligible, total, positive, negative, details_json, timestamp)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (rt, eligible, total, positive, negative, details_json, ts),
    )
    run_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()
    return run_id


def get_retraining_runs(limit=50):
    """Return recent retraining runs."""
    init_db()
    conn = connect()
    rows = conn.execute(
        """SELECT id, run_type, eligible, total, positive, negative, details_json, timestamp
           FROM retraining_runs ORDER BY id DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_retraining_run(run_id, eligible=None, total=None, status=None, **kwargs):
    """Update a retraining run record."""
    init_db()
    conn = connect()
    updates = []
    params = []
    if eligible is not None:
        updates.append("eligible = ?")
        params.append(eligible)
    if total is not None:
        updates.append("total = ?")
        params.append(total)
    if status is not None:
        updates.append("status = ?")
        params.append(status)
    # Handle additional kwargs
    if kwargs.get("n_feedback") is not None:
        updates.append("eligible = ?")
        params.append(kwargs["n_feedback"])
    if kwargs.get("finished_at") is not None:
        pass  # timestamp already exists
    if kwargs.get("notes") is not None:
        pass  # no notes column, store in details_json
    if kwargs.get("n_positive") is not None:
        updates.append("positive = ?")
        params.append(kwargs["n_positive"])
    if kwargs.get("n_negative") is not None:
        updates.append("negative = ?")
        params.append(kwargs["n_negative"])
    if not updates:
        conn.close()
        return
    params.append(run_id)
    q = f"UPDATE retraining_runs SET {', '.join(updates)} WHERE id = ?"
    conn.execute(q, params)
    conn.commit()
    conn.close()


def _compute_psi(expected, actual):
    """Compute Population Stability Index between two distributions."""
    import numpy as np
    try:
        import numpy as np
        if len(expected) == 0 or len(actual) == 0:
            return None
        expected = np.array(expected, dtype=float)
        actual = np.array(actual, dtype=float)
        # Create bins covering [0, 1]
        bins = np.linspace(0, 1, 11)  # 10 bins
        # Compute histograms
        expected_hist, _ = np.histogram(expected, bins=bins)
        actual_hist, _ = np.histogram(actual, bins=bins)
        # Convert to proportions
        expected_props = expected_hist / expected_hist.sum()
        actual_props = actual_hist / actual_hist.sum()
        # Avoid log(0) by replacing 0 with small value
        eps = 1e-6
        expected_props = np.maximum(expected_props, eps)
        actual_props = np.maximum(actual_props, eps)
        # PSI = sum((actual - expected) * ln(actual / expected))
        psi = np.sum((actual_props - expected_props) * np.log(actual_props / expected_props))
        return float(psi)
    except Exception:
        return None


def _histogram(rows):
    """Return score histogram bins for monitoring."""
    scores = [float(r["score"]) for r in rows if r["score"] is not None]
    bins = {f"bin_{i}": 0 for i in range(10)}
    if scores:
        from numpy import linspace, histogram
        hist, bin_edges = histogram(scores, bins=linspace(0, 1, 11))
        for i in range(len(hist)):
            bins[f"bin_{i}"] = int(hist[i])
    return bins


def _psi(prev, cur):
    """Compute PSI between previous and current score distributions.

    prev and cur are aggregation dicts from _agg that may contain
    a 'scores' key or histogram data.  Returns None if insufficient data.
    """
    prev_scores = []
    cur_scores = []
    # Try to extract scores from the aggregation results
    # If prev/cur have 'hist' (bin counts), reconstruct scores approximately
    # or just return None for PSI when we only have binned data
    if "hist" in cur and "hist" in prev:
        # We have histogram data - compute PSI from histogram bins
        try:
            import numpy as np
            prev_hist = np.array([prev["hist"].get(f"bin_{i}", 0) for i in range(10)], dtype=float)
            cur_hist = np.array([cur["hist"].get(f"bin_{i}", 0) for i in range(10)], dtype=float)
            if prev_hist.sum() == 0 or cur_hist.sum() == 0:
                return None
            prev_props = prev_hist / prev_hist.sum()
            cur_props = cur_hist / cur_hist.sum()
            eps = 1e-6
            prev_props = np.maximum(prev_props, eps)
            cur_props = np.maximum(cur_props, eps)
            # Correct PSI formula: sum((actual - expected) * ln(actual/expected))
            # where actual = cur_props, expected = prev_props
            psi2 = np.sum((cur_props - prev_props) * np.log(cur_props / prev_props))
            return float(psi2)
        except Exception:
            return None
    # If we have raw scores, use them
    if "avg_score" in cur:
        cur_scores = [cur["avg_score"]]  # simplified
    if "avg_score" in prev:
        prev_scores = [prev["avg_score"]]
    if prev_scores and cur_scores:
        try:
            import numpy as np
            bins = np.linspace(0, 1, 11)
            prev_hist, _ = np.histogram(prev_scores, bins=bins)
            cur_hist, _ = np.histogram(cur_scores, bins=bins)
            prev_props = prev_hist / prev_hist.sum()
            cur_props = cur_hist / cur_hist.sum()
            eps = 1e-6
            prev_props = np.maximum(prev_props, eps)
            cur_props = np.maximum(cur_props, eps)
            psi = np.sum((cur_props - prev_props) * np.log(cur_props / prev_props))
            return float(psi)
        except Exception:
            return None
    return None


def get_active_learning(limit=50, low=UNCERTAIN_LOW, high=UNCERTAIN_HIGH):
    """Return uncertain predictions queue with priority ordering."""
    init_db()
    conn = connect()
    count = conn.execute(
        """SELECT COUNT(*) AS n FROM predictions
           WHERE score BETWEEN ? AND ?
            AND (user_feedback IS NULL OR user_feedback='unknown')""",
        (float(low), float(high)),
    ).fetchone()["n"]
    # Order by uncertainty (distance from 0.5) then by recency
    rows = conn.execute(
        """SELECT id, url, verdict, score, model_version, variant, timestamp
           FROM predictions
           WHERE score BETWEEN ? AND ?
             AND (user_feedback IS NULL OR user_feedback='unknown')
           ORDER BY ABS(score - 0.5) ASC, id DESC LIMIT ?""",
        (float(low), float(high), int(limit)),
    ).fetchall()
    conn.close()
    # If very few items, still return what we have (minimum 1 if any exist)
    items = [dict(r) for r in rows]
    if count == 0 and items:
        count = len(items)
    return {
        "low": low, "high": high, "count": int(count), "items": items
    }


def get_monitoring(window_days=7):
    """Return monitoring data with corrected domain drift logic."""
    init_db()
    conn = connect()
    rows = [dict(r) for r in conn.execute(
        """SELECT verdict, score, user_feedback, timestamp, registrable_domain, variant
           FROM predictions ORDER BY id DESC"""
    ).fetchall()]
    conn.close()
    now = datetime.now(timezone.utc)
    cut_now = now - timedelta(days=window_days)
    cut_prev = now - timedelta(days=2 * window_days)

    def parse_ts(value):
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except Exception:
            return None

    current, previous = [], []
    for r in rows:
        ts = parse_ts(r["timestamp"])
        if ts is None:
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        if ts >= cut_now:
            current.append(r)
        elif ts >= cut_prev:
            previous.append(r)

    # Fixed domain drift: insufficient_data when no historical baseline
    current_domains = {r["registrable_domain"] for r in current if r["registrable_domain"]}
    previous_domains = {r["registrable_domain"] for r in previous if r["registrable_domain"]}
    domain_drift = _compute_domain_drift(current_domains, previous_domains, len(current))

    cur = _agg(current)
    prev = _agg(previous)
    cur["hist"] = _histogram(current)
    prev["hist"] = _histogram(previous)
    psi = _psi(prev, cur)
    drift_status = "insufficient_data" if psi is None else ("drift" if psi > 0.25 else "stable")

    # Build daily activity
    daily = {}
    for r in current:
        ts = parse_ts(r["timestamp"])
        if ts:
            key = ts.date().isoformat()
            daily.setdefault(key, {"date": key, "n": 0, "feedback": 0, "incorrect": 0})
            daily[key]["n"] += 1
            if r["user_feedback"]:
                daily[key]["feedback"] += 1
            if r["user_feedback"] == "incorrect":
                daily[key]["incorrect"] += 1

    alerts = []
    if cur["feedback"] >= MIN_FEEDBACK_FOR_ALERT and cur["incorrect_rate"] > ALERT_INCORRECT_RATE:
        alerts.append({
            "type": "feedback_error_rate", "severity": "high",
            "message": f"Taux de feedback incorrect {cur['incorrect_rate']*100:.1f}% > 5% sur {cur['feedback']} retours."
        })
    if domain_drift["status"] == "drift":
        alerts.append({
            "type": "data_drift", "severity": "medium",
            "message": f"Data drift détecté (PSI={psi})."
        })
    if domain_drift["status"] == "drift":
        alerts.append({
            "type": "domain_drift", "severity": "medium",
            "message": f"{domain_drift['new_domain_ratio']*100:.1f}% des domaines récents sont nouveaux."
        })

    return {
        "window_days": window_days,
        "current": cur,
        "previous": prev,
        "psi": psi,
        "drift_status": drift_status,
        "domain_drift": domain_drift,
        "daily": sorted(daily.values(), key=lambda x: x["date"]),
        "alerts": alerts,
        "alert_threshold": ALERT_INCORRECT_RATE,
        "min_feedback_for_alert": MIN_FEEDBACK_FOR_ALERT,
    }


def get_history(limit=100, offset=0, days=30):
    """Return historical predictions for the given number of days."""
    init_db()
    conn = connect()
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    cutoff_iso = cutoff.isoformat()
    rows = conn.execute(
        """SELECT id, url, verdict, score, user_feedback, variant, model_version, timestamp, registrable_domain
           FROM predictions WHERE timestamp > ? ORDER BY id DESC LIMIT ? OFFSET ?""",
        (cutoff_iso, limit, offset),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def now_iso():
    """Return current ISO timestamp."""
    return datetime.now(timezone.utc).isoformat()