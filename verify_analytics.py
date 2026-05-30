import sqlite3
import os
import shutil
import database
import pandas as pd
from datetime import datetime

# Use a test DB
TEST_DB = "data/test_analytics.db"
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)
database.DB_PATH = TEST_DB

from database import create_table, create_event, add_staff, update_event_status
from analytics import calculate_staff_insights, get_department_trends, predict_event_success

print("--- Setting up Test Data ---")
create_table()

# Staff
add_staff("Regular User", "IT", "Dev") # Should have 100%
add_staff("Absent User", "HR", "Mgr")  # Should have 0%
add_staff("Late User", "IT", "Dev")    # 50% but late

conn = sqlite3.connect(TEST_DB)
c = conn.cursor()

# Get Staff IDs
c.execute("SELECT id, name FROM staff")
staff_map = {name: sid for sid, name in c.fetchall()}

# Create 2 Completed Events
c.execute("INSERT INTO events (name, date, time, end_time, status) VALUES (?, ?, ?, ?, ?)", 
          ("Event 1", "2026-01-01", "09:00:00", "10:00:00", "Completed"))
e1_id = c.lastrowid

c.execute("INSERT INTO events (name, date, time, end_time, status) VALUES (?, ?, ?, ?, ?)", 
          ("Event 2", "2026-01-08", "09:00:00", "10:00:00", "Completed"))
e2_id = c.lastrowid
conn.commit()

# Attendance
# Regular User: Both events, on time
c.execute("INSERT INTO event_attendance (event_id, staff_id, staff_name, check_in_time, exit_time) VALUES (?, ?, ?, ?, ?)",
          (e1_id, staff_map["Regular User"], "Regular User", "09:00:00", "10:00:00"))
c.execute("INSERT INTO event_attendance (event_id, staff_id, staff_name, check_in_time, exit_time) VALUES (?, ?, ?, ?, ?)",
          (e2_id, staff_map["Regular User"], "Regular User", "08:55:00", "10:05:00"))

# Late User: Only 1 event, late
c.execute("INSERT INTO event_attendance (event_id, staff_id, staff_name, check_in_time, exit_time) VALUES (?, ?, ?, ?, ?)",
          (e1_id, staff_map["Late User"], "Late User", "09:15:00", "10:00:00"))
conn.commit()
conn.close()

from database import get_all_attendance_flat, get_all_past_events
print(f"DEBUG: Past Events: {len(get_all_past_events())}")
print(f"DEBUG: Attendance Records: {len(get_all_attendance_flat())}")
print(f"DEBUG: Raw Record Sample: {get_all_attendance_flat()[0] if get_all_attendance_flat() else 'None'}")

print("\n--- Testing Staff Insights ---")
df = calculate_staff_insights()
if not df.empty:
    # Clean status for printing to avoid encoding errors
    df_print = df[["Staff Name", "Attendance %", "Late Arrivals", "Status"]].copy()
    df_print["Status"] = df_print["Status"].apply(lambda x: x.encode('ascii', 'ignore').decode('ascii'))
    print(df_print.to_string())
    
    # Assertions
    reg = df[df["Staff Name"] == "Regular User"].iloc[0]
    assert reg["Attendance %"] == "100.0%", "Regular User should be 100%"
    assert "Low Risk" in reg["Status"], "Regular User should be Low Risk"
    
    absent = df[df["Staff Name"] == "Absent User"].iloc[0]
    assert absent["Attendance %"] == "0.0%", "Absent User should be 0%"
    assert "High Risk" in absent["Status"], "Absent User should be High Risk"
    
    late = df[df["Staff Name"] == "Late User"].iloc[0]
    assert late["Attendance %"] == "50.0%", "Late User should be 50%"
    assert late["Late Arrivals"] == 1, "Late User should have 1 late"
    
    print("OK: Staff Metrics Verified")
else:
    print("FAIL: No insights generated")

print("\n--- Testing Department Trends ---")
trends = get_department_trends()
print(trends)
# IT: (100 + 50) / 2 = 75%
# HR: 0%
# (Approx check)

print("\n--- Testing Event Prediction ---")
# Predict for a Thursday (2026-01-15) - same weekday as test events
pred = predict_event_success("2026-01-15")
# Strip unicode from prediction for printing
pred_safe = pred.encode('ascii', 'ignore').decode('ascii')
print(f"Prediction: {pred_safe}")

if "Expected Turnout" in pred:
    print("OK: Prediction generated")
else:
    print("FAIL: Prediction failed")
