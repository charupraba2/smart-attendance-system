
import sqlite3
import os

DB_PATH = "data/attendance.db"

if not os.path.exists(DB_PATH):
    print(f"Error: {DB_PATH} not found.")
else:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        # List all tables
        c.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = c.fetchall()
        print("Tables found:", [t[0] for t in tables])
        
        for table in tables:
            t_name = table[0]
            print(f"\nSchema for {t_name}:")
            c.execute(f"PRAGMA table_info({t_name})")
            columns = c.fetchall()
            for col in columns:
                print(col)
    except Exception as e:
        print(f"Error reading schema: {e}")
    finally:
        conn.close()
