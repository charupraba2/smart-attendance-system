
import sqlite3
import os

DB_PATH = "data/attendance.db"

if not os.path.exists(DB_PATH):
    print(f"Error: {DB_PATH} not found.")
else:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("PRAGMA table_info(attendance)")
        columns = c.fetchall()
        print("Attendance Table Columns:")
        for col in columns:
            print(col)
    except Exception as e:
        print(f"Error reading schema: {e}")
    finally:
        conn.close()
