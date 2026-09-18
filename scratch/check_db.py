import sqlite3
import os

db_path = 'sanchay_local.db'
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found")
else:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print("Tables in DB:", [t[0] for t in tables])
    
    for table in [t[0] for t in tables]:
        try:
            count = cur.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            print(f"Table {table}: {count} rows")
        except Exception as e:
            print(f"Error reading {table}: {e}")
    conn.close()
