from database import create_table, add_staff, create_event, get_events, mark_event_attendance_by_name, get_event_attendance
import sqlite3

def test_auto_attendance():
    print("Running Auto-Attendance Verification...")
    create_table()
    
    # Setup
    staff_name = "Auto Staff"
    add_staff(staff_name, "AI", "Bot")
    
    event_name = "Auto Event"
    create_event(event_name, "2023-11-01", "09:00")
    
    # Get IDs
    conn = sqlite3.connect("data/attendance.db")
    c = conn.cursor()
    c.execute("SELECT id FROM staff WHERE name=?", (staff_name,))
    s_id = c.fetchone()[0]
    c.execute("SELECT id FROM events WHERE name=?", (event_name,))
    e_id = c.fetchone()[0]
    conn.close()
    
    # Test Marking by Name
    print(f"Marking attendance for {staff_name} in event {event_name}...")
    success, msg = mark_event_attendance_by_name(e_id, staff_name)
    print(f"Result: {success}, {msg}")
    
    assert success == True
    assert "Attendance marked" in msg
    
    # Verify in DB
    attended_ids = get_event_attendance(e_id)
    assert s_id in attended_ids
    
    # Test Duplicate
    print("Testing duplicate marking...")
    success, msg = mark_event_attendance_by_name(e_id, staff_name)
    print(f"Result: {success}, {msg}")
    assert success == False
    assert "already marked" in msg

    print("AUTO-ATTENDANCE TESTS PASSED")

if __name__ == "__main__":
    test_auto_attendance()
