import sqlite3
con = sqlite3.connect("D:/openhands/projects/v2/phishing_ai_master/database/predictions.db")
print("integrity_check:", con.execute("PRAGMA integrity_check").fetchone())
print("tables:", [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()])
for t in ["predictions", "feedback", "retraining_runs", "monitoring_events"]:
    print(t, "count=", con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
print("indexes predictions:", [r[1] for r in con.execute("PRAGMA index_list(predictions)").fetchall()])
con.close()
