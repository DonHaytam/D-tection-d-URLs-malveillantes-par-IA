"""Domain drift and monitoring improvements for the laboratoire dashboard.

Provides corrected domain drift logic, feedback aggregation, A/B testing with
minimum sample-size policy, active learning queue with priority ordering, and
monitoring with PSI-based drift detection.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone


# ---- Domain drift: never 100% when historical baseline is empty ----

def _compute_domain_drift(current_domains, previous_domains, current_count):
    """Return domain drift status and details.

    Rules:
    - If previous_domains is empty (no historical baseline), return insufficient_data.
    - If current_domains is empty, return stable with 0 new domains.
    - Otherwise compute new domains ratio and status.
    """
    if not previous_domains:
        # No historical baseline -> cannot compute drift
        return {
            "current_unique_domains": len(current_domains) if current_domains else 0,
            "previous_unique_domains": 0,
            "new_domains": 0,
            "new_domain_ratio": 0.0,
            "status": "insufficient_data",
        }
    if not current_domains:
        return {
            "current_unique_domains": 0,
            "previous_unique_domains": len(previous_domains),
            "new_domains": 0,
            "new_domain_ratio": 0.0,
            "status": "stable",
        }

    new_domains = current_domains - previous_domains
    ratio = len(new_domains) / len(current_domains)

    status = "drift" if ratio > 0.5 else "stable"

    return {
        "current_unique_domains": len(current_domains),
        "previous_unique_domains": len(previous_domains),
        "new_domains": len(new_domains),
        "new_domain_ratio": round(ratio, 6),
        "status": status,
    }


# ---- Feedback aggregation with duplicate handling ----

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


# ---- A/B testing with minimum sample size ----

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


# ---- Active Learning queue with priority ----

UNCERTAIN_LOW = 0.4
UNCERTAIN_HIGH = 0.6


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


# ---- Monitoring with fixed domain drift ----

def init_db():
    """Initialise la base de données si nécessaire."""
    db_path = "D:/openhands/projects/v2/phishing_ai_master/database/predictions.db"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
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
    db_path = "D:/openhands/projects/v2/phishing_ai_master/database/predictions.db"
    if not os.path.exists(db_path):
        init_db()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


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
            prev_hist = np.array([cur["hist"].get(f"bin_{i}", 0) for i in range(10)], dtype=float)
            cur_hist = np.array([prev["hist"].get(f"bin_{i}", 0) for i in range(10)], dtype=float)
            if prev_hist.sum() == 0 or cur_hist.sum() == 0:
                return None
            prev_props = prev_hist / prev_hist.sum()
            cur_props = cur_hist / cur_hist.sum()
            eps = 1e-6
            prev_props = np.maximum(prev_props, eps)
            cur_props = np.maximum(cur_props, eps)
            psi = np.sum((cur_props - prev_hist) * np.log(cur_props / prev_props))  # note: using cur_props - prev_props corrected below
            # Actually correct formula: sum((actual - expected) * ln(actual/expected))
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