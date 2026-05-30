from database import create_table, add_staff, create_event, get_events, mark_event_attendance_face, get_event_report
import sqlite3

def test_refactor():
    print("Running Refactor Verification...")
    create_table()
    
    # 1. Add Staff
    staff_name = "Refactor Staff"
    add_staff(staff_name, "TEST", "TEST")
    
    # 2. Create Event
    event_name = "Refactor Event"
    create_event(event_name, "2024-01-01", "12:00")
    
    # Get IDs
    conn = sqlite3.connect("data/attendance.db")
    c = conn.cursor()
    c.execute("SELECT id FROM events WHERE name=?", (event_name,))
    e_id = c.fetchone()[0]
    conn.close()
    
    # 3. Mark Attendance (Face)
    print("Marking attendance...")
    success, msg = mark_event_attendance_face(e_id, staff_name)
    print(f"Result: {success}, {msg}")
    assert success == True
    
    # 4. Check Report (Timestamps)
    print("Checking report...")
    report = get_event_report(e_id)
    print(f"Report: {report}")
    assert len(report) > 0
    # report[0] -> (EventName, Date, Time, Staff, Dept, Desg, Status)
    # Check if we have check-in time
    assert report[0][2] is not None # Check-in Time
    
    print("REFACTOR TESTS PASSED")

if __name__ == "__main__":
    test_refactor()
