import sqlite3
import os
import shutil
import database

# Use a test DB
TEST_DB = "data/test_search.db"
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)
database.DB_PATH = TEST_DB

from database import get_filtered_attendance, create_table, create_event, add_staff, mark_event_attendance_face

print("--- Setting up Test Data ---")
create_table()
add_staff("Test Staff", "IT", "Tester")
create_event("Test Live Event", "2026-05-20", "09:00", "18:00")
# We need to simulate attendance
# Since we don't have events id easily without get_events, let's fetch it
conn = sqlite3.connect(TEST_DB)
c = conn.cursor()
c.execute("SELECT id FROM events LIMIT 1")
eid = c.fetchone()[0]
conn.close()

mark_event_attendance_face(eid, "Test Staff")

print("--- Testing Unified Search ---")

def test_query(term, description):
    print(f"\nQuery: '{term}' ({description})")
    results = get_filtered_attendance(search_query=term)
    if results:
        print(f"OK: Found {len(results)} records.")
        r = results[0] # Event, Date, Time, Exit, Staff, Dept...
        print(f"   Sample: {r[0]} | {r[4]} | {r[1]}")
    else:
        print("FAIL: No records found.")

# We assume 'Test Staff' and 'Test Live Event' exist from previous steps or manual usage.
# If not, this test might fail efficiently.

test_query("Test", "Partial Name")
test_query("2026", "Year")
test_query("Event", "Partial Event Name")
test_query("IT", "Department (if set)")
test_query("NonExistent", "Should fail")
