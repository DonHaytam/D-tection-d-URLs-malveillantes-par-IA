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

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
DEFAULT_DB_PATH = os.path.join(ROOT, "database", "predictions.db")
DEFAULT_DB_PATH = os.environ.get("DB_PATH", DEFAULT_DB_PATH)

FEEDBACK_VALUES = {"correct", "incorrect", "unknown"}
CORRECTED_LABELS = {"phishing", "legitimate", None}
UNCERTAIN_LOW = 0.4
UNCERTAIN_HIGH = 0.6
ALERT_INCORRECT_RATE = 0.05
MIN_FEEDBACK_FOR_ALERT = 20


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def db_path():
    return os.environ.get("DB_PATH", DEFAULT_DB_PATH)


def connect():
    path = db_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_db():
    conn = connect()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL,
        verdict TEXT,
        score REAL,
        model_version TEXT,
        thresholds TEXT,
        processing_time_ms REAL,
        timestamp TEXT NOT NULL,
        user_feedback TEXT DEFAULT NULL,
        feedback_timestamp TEXT DEFAULT NULL
    )""")
    existing = {row["name"] for row in c.execute("PRAGMA table_info(predictions)").fetchall()}
    migrations = {
        "corrected_label": "TEXT DEFAULT NULL",
        "feedback_comment": "TEXT DEFAULT NULL",
        "explanation": "TEXT DEFAULT NULL",
        "variant": "TEXT DEFAULT NULL",
        "client_id": "TEXT DEFAULT NULL",
        "normalized_url": "TEXT DEFAULT NULL",
        "registrable_domain": "TEXT DEFAULT NULL",
    }
    for col, ddl in migrations.items():
        if col not in existing:
            c.execute(f"ALTER TABLE predictions ADD COLUMN {col} {ddl}")
    c.execute("CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON predictions(timestamp)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_predictions_score ON predictions(score)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_predictions_variant ON predictions(variant)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_predictions_feedback ON predictions(user_feedback)")
    c.execute("""CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prediction_id INTEGER NOT NULL,
        feedback TEXT NOT NULL,
        corrected_label TEXT,
        comment TEXT,
        created_at TEXT NOT NULL,
        UNIQUE(prediction_id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS retraining_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        trigger TEXT,
        status TEXT NOT NULL,
        n_feedback INTEGER DEFAULT 0,
        n_train INTEGER DEFAULT 0,
        n_positive INTEGER DEFAULT 0,
        n_negative INTEGER DEFAULT 0,
        metrics_json TEXT,
        artifact_path TEXT,
        approved INTEGER DEFAULT 0,
        approved_at TEXT,
        notes TEXT,
        finished_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS monitoring_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        event_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        message TEXT NOT NULL,
        details TEXT
    )""")
    c.execute("CREATE INDEX IF NOT EXISTS idx_monitoring_created ON monitoring_events(created_at)")
    conn.commit()
    conn.close()


def _safe_domain(url):
    try:
        from src.data.validation import extract_components
        host = extract_components(url)["host"]
        return registrable_domain(host)
    except Exception:
        return None


def save_prediction(url, result, explanation=None, variant=None, client_id=None):
    init_db()
    ts = now_iso()
    norm = normalize_url(url)
    rd = _safe_domain(url)
    conn = connect()
    c = conn.cursor()
    c.execute(
        """INSERT INTO predictions
           (url, verdict, score, model_version, thresholds, processing_time_ms,
            timestamp, explanation, variant, client_id, normalized_url, registrable_domain)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            str(url),
            str(result.get("verdict")),
            float(result.get("score", 0.0)),
            str(result.get("model_version")),
            json.dumps(result.get("thresholds", {})),
            float(result.get("processing_time_ms", 0.0)),
            ts,
            json.dumps(explanation, default=str) if explanation is not None else None,
            variant,
            client_id,
            norm,
            rd,
        ),
    )
    rid = int(c.lastrowid)
    conn.commit()
    conn.close()
    return rid, ts


def get_prediction(prediction_id):
    init_db()
    conn = connect()
    row = conn.execute("SELECT * FROM predictions WHERE id = ?", (int(prediction_id),)).fetchone()
    conn.close()
    return dict(row) if row else None


def set_feedback(prediction_id, feedback, corrected_label=None, comment=None):
    if feedback not in FEEDBACK_VALUES:
        raise ValueError("feedback must be correct, incorrect or unknown")
    if corrected_label not in CORRECTED_LABELS:
        raise ValueError("corrected_label must be phishing, legitimate or null")
    init_db()
    conn = connect()
    row = conn.execute("SELECT id FROM predictions WHERE id = ?", (int(prediction_id),)).fetchone()
    if row is None:
        conn.close()
        raise KeyError("prediction not found")
    ts = now_iso()
    conn.execute(
        """UPDATE predictions
           SET user_feedback=?, feedback_timestamp=?, corrected_label=?, feedback_comment=?
           WHERE id=?""",
        (feedback, ts, corrected_label, comment, int(prediction_id)),
    )
    conn.execute(
        """INSERT INTO feedback (prediction_id, feedback, corrected_label, comment, created_at)
           VALUES (?,?,?,?,?)
           ON CONFLICT(prediction_id) DO UPDATE SET
             feedback=excluded.feedback,
             corrected_label=excluded.corrected_label,
             comment=excluded.comment,
             created_at=excluded.created_at""",
        (int(prediction_id), feedback, corrected_label, comment, ts),
    )
    conn.commit()
    conn.close()
    return feedback_summary()


def _row_to_dict(row):
    d = dict(row)
    if d.get("explanation"):
        try:
            d["explanation"] = json.loads(d["explanation"])
        except Exception:
            pass
    if d.get("thresholds"):
        try:
            d["thresholds"] = json.loads(d["thresholds"])
        except Exception:
            pass
    return d


def get_history(limit=100, offset=0):
    init_db()
    conn = connect()
    rows = conn.execute(
        """SELECT id, url, verdict, score, model_version, variant, timestamp,
                  user_feedback, corrected_label, feedback_timestamp, processing_time_ms
           FROM predictions ORDER BY id DESC LIMIT ? OFFSET ?""",
        (int(limit), int(offset)),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_feedback_rows(limit=500):
    init_db()
    conn = connect()
    rows = conn.execute(
        """SELECT id, url, verdict, score, model_version, variant, timestamp,
                  user_feedback, corrected_label, feedback_comment, feedback_timestamp
           FROM predictions
           WHERE user_feedback IS NOT NULL
           ORDER BY feedback_timestamp DESC, id DESC LIMIT ?""",
        (int(limit),),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _cutoff(days):
    return (datetime.now(timezone.utc) - timedelta(days=days)).replace(microsecond=0).isoformat()


def feedback_summary():
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
    }


def _agg(rows):
    n = len(rows)
    if n == 0:
        return {"n": 0, "feedback": 0, "correct": 0, "incorrect": 0, "unknown": 0,
                "incorrect_rate": 0.0, "avg_score": None}
    fb = [r for r in rows if r["user_feedback"]]
    incorrect = sum(1 for r in fb if r["user_feedback"] == "incorrect")
    correct = sum(1 for r in fb if r["user_feedback"] == "correct")
    unknown = sum(1 for r in fb if r["user_feedback"] == "unknown")
    scores = [float(r["score"]) for r in rows if r["score"] is not None]
    return {
        "n": n,
        "feedback": len(fb),
        "correct": correct,
        "incorrect": incorrect,
        "unknown": unknown,
        "incorrect_rate": round(incorrect / len(fb), 6) if fb else 0.0,
        "avg_score": round(sum(scores) / len(scores), 6) if scores else None,
    }


def _histogram(rows, bins=10):
    counts = [0] * bins
    for r in rows:
        s = r["score"]
        if s is None:
            continue
        idx = min(bins - 1, max(0, int(float(s) * bins)))
        counts[idx] += 1
    total = sum(counts)
    return [{"bin": f"{i / bins:.1f}-{(i + 1) / bins:.1f}", "count": c,
             "share": round(c / total, 6) if total else 0.0} for i, c in enumerate(counts)]


def _psi(prev, curr, bins=10, eps=1e-6):
    if prev["n"] < 20 or curr["n"] < 20:
        return None
    p = [max(eps, x["share"]) for x in prev["hist"]]
    q = [max(eps, x["share"]) for x in curr["hist"]]
    return round(sum((a - b) * math.log(a / b) for a, b in zip(p, q)), 6)


def get_stats():
    init_db()
    conn = connect()
    rows = [dict(r) for r in conn.execute(
        "SELECT verdict, score, user_feedback, timestamp, registrable_domain FROM predictions"
    ).fetchall()]
    conn.close()
    summary = _agg(rows)
    verdicts = {}
    for r in rows:
        verdicts[r["verdict"] or "UNKNOWN"] = verdicts.get(r["verdict"] or "UNKNOWN", 0) + 1
    summary["verdicts"] = verdicts
    summary["score_histogram"] = _histogram(rows)
    summary["active_learning_pending"] = len(get_active_learning(limit=1000)["items"])
    return summary


def get_active_learning(limit=50, low=UNCERTAIN_LOW, high=UNCERTAIN_HIGH):
    init_db()
    conn = connect()
    count = conn.execute(
        """SELECT COUNT(*) AS n FROM predictions
           WHERE score BETWEEN ? AND ?
             AND (user_feedback IS NULL OR user_feedback='unknown')""",
        (float(low), float(high)),
    ).fetchone()["n"]
    rows = conn.execute(
        """SELECT id, url, verdict, score, model_version, variant, timestamp
           FROM predictions
           WHERE score BETWEEN ? AND ?
             AND (user_feedback IS NULL OR user_feedback='unknown')
           ORDER BY ABS(score - 0.5) ASC, id DESC LIMIT ?""",
        (float(low), float(high), int(limit)),
    ).fetchall()
    conn.close()
    return {"low": low, "high": high, "count": int(count), "items": [dict(r) for r in rows]}


def get_monitoring(window_days=7):
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

    cur = _agg(current)
    prev = _agg(previous)
    cur["hist"] = _histogram(current)
    prev["hist"] = _histogram(previous)
    psi = _psi(prev, cur)
    drift_status = "insufficient_data" if psi is None else ("drift" if psi > 0.25 else "stable")

    prev_domains = {r["registrable_domain"] for r in previous if r["registrable_domain"]}
    cur_domains = {r["registrable_domain"] for r in current if r["registrable_domain"]}
    new_domains = cur_domains - prev_domains
    domain_drift = {
        "current_unique_domains": len(cur_domains),
        "previous_unique_domains": len(prev_domains),
        "new_domains": len(new_domains),
        "new_domain_ratio": round(len(new_domains) / len(cur_domains), 6) if cur_domains else 0.0,
        "status": "insufficient_data" if len(current) < 20 else ("drift" if cur_domains and len(new_domains) / len(cur_domains) > 0.5 else "stable"),
    }

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
        alerts.append({"type": "feedback_error_rate", "severity": "high",
                       "message": f"Taux de feedback incorrect {cur['incorrect_rate']*100:.1f}% > 5% "
                                  f"sur {cur['feedback']} retours."})
    if drift_status == "drift":
        alerts.append({"type": "data_drift", "severity": "medium",
                       "message": f"Data drift detecte (PSI={psi})."})
    if domain_drift["status"] == "drift":
        alerts.append({"type": "domain_drift", "severity": "medium",
                       "message": f"{domain_drift['new_domain_ratio']*100:.1f}% des domaines recents sont nouveaux."})
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


def get_ab_test():
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
            verdicts[r["verdict"] or "UNKNOWN"] = verdicts.get(r["verdict"] or "UNKNOWN", 0) + 1
        a["verdicts"] = verdicts
        out[variant] = a
    winner = "insufficient_data"
    if "M1" in out and "ENSEMBLE" in out:
        if out["M1"]["feedback"] >= 20 and out["ENSEMBLE"]["feedback"] >= 20:
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


def create_retraining_run(trigger="manual", notes=None):
    init_db()
    conn = connect()
    c = conn.cursor()
    c.execute("INSERT INTO retraining_runs (created_at, trigger, status, notes) VALUES (?,?,?,?)",
              (now_iso(), trigger, "running", notes))
    rid = int(c.lastrowid)
    conn.commit()
    conn.close()
    return rid


def update_retraining_run(run_id, **fields):
    allowed = {"status", "n_feedback", "n_train", "n_positive", "n_negative", "metrics_json",
               "artifact_path", "approved", "approved_at", "notes", "finished_at"}
    sets, vals = [], []
    for key, value in fields.items():
        if key in allowed:
            sets.append(f"{key}=?")
            vals.append(value)
    if not sets:
        return
    vals.append(int(run_id))
    conn = connect()
    conn.execute(f"UPDATE retraining_runs SET {', '.join(sets)} WHERE id=?", vals)
    conn.commit()
    conn.close()


def get_retraining_runs(limit=20):
    init_db()
    conn = connect()
    rows = conn.execute("SELECT * FROM retraining_runs ORDER BY id DESC LIMIT ?", (int(limit),)).fetchall()
    conn.close()
    out = []
    for r in rows:
        d = dict(r)
        if d.get("metrics_json"):
            try:
                d["metrics"] = json.loads(d["metrics_json"])
            except Exception:
                d["metrics"] = None
        out.append(d)
    return out


def get_last_retraining_run():
    runs = get_retraining_runs(limit=1)
    return runs[0] if runs else None


def log_event(event_type, severity, message, details=None):
    init_db()
    conn = connect()
    conn.execute("INSERT INTO monitoring_events (created_at, event_type, severity, message, details) VALUES (?,?,?,?,?)",
                 (now_iso(), event_type, severity, message,
                  json.dumps(details, default=str) if details is not None else None))
    conn.commit()
    conn.close()


def get_events(limit=50):
    init_db()
    conn = connect()
    rows = conn.execute("SELECT * FROM monitoring_events ORDER BY id DESC LIMIT ?", (int(limit),)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
