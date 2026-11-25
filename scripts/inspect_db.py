import sqlite3
p = "D:/openhands/projects/v2/phishing_ai_master/database/predictions.db"
con = sqlite3.connect(p)
rows = con.execute("select name, sql from sqlite_master where type='table'").fetchall()
for name, sql in rows:
    print("TABLE", name)
    print(sql)
    print("count", con.execute(f"select count(*) from {name}").fetchone()[0])
con.close()
