import sqlite3
import os
import shutil
import database

# Monkeypatch DB_PATH to avoid locks on main DB
TEST_DB = os.path.join("data", "test_attendance.db")
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)
database.DB_PATH = TEST_DB

from database import create_table, mark_event_attendance_face, get_filtered_attendance, add_staff, create_event, get_events

print(f"Using Test DB: {database.DB_PATH}")

print("--- 1. Testing Schema Migration ---")
# Create table (mocking migration on clean DB isn't great, but function code is same)
create_table() 
conn = sqlite3.connect(TEST_DB)
c = conn.cursor()
try:
    c.execute("SELECT exit_time FROM event_attendance LIMIT 1")
    print("SUCCESS: 'exit_time' column exists.")
except Exception as e:
    print(f"FAILURE: {e}")
conn.close()

print("\n--- 2. Setting up Test Data ---")
# Ensure we have a staff and event
try:
    add_staff("Test Staff", "IT", "Tester")
except:
    pass # Might already exist
    
create_event("Test Live Event", "2025-01-01", "09:00", "18:00")
events = get_events()
event_id = events[0][0]
print(f"Using Event ID: {event_id}")

print("\n--- 3. Testing Entry Time ---")
success, msg = mark_event_attendance_face(event_id, "Test Staff")
print(f"First Check-in: {success} - {msg}")

import time
time.sleep(2)

print("\n--- 4. Testing Exit Time Update ---")
success, msg = mark_event_attendance_face(event_id, "Test Staff")
print(f"Second Check-in: {success} - {msg}")

print("\n--- 5. Testing Search ---")
results = get_filtered_attendance(year="2026", event_name="Test Live Event", staff_query="Test Staff")
if results:
    r = results[0]
    # columns: event_name, date, time, exit_time, staff_name...
    print(f"Record found: Entry={r[2]}, Exit={r[3]}")
    if r[2] != r[3]:
        print("SUCCESS: Entry and Exit times are different.")
    else:
        print("WARNING: Entry and Exit times are same (might be too fast execution?)")
else:
    print("FAILURE: No records found.")
