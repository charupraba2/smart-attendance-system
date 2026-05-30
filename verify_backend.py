from database import create_table, add_staff, get_all_staff, create_event, get_events, mark_event_attendance, get_event_attendance, get_full_event_report
import sqlite3
import os

def test_verification():
    print("running verification...")
    # Ensure tables exist
    create_table()
    
    # Test 1: Add Staff
    print("Testing Add Staff...")
    staff_name = "Test Staff"
    add_staff(staff_name, "CS", "Professor")
    staff = get_all_staff()
    print(f"Staff List: {staff}")
    assert any(s[1] == staff_name for s in staff), "Staff not added"

    # Test 2: Create Event
    print("Testing Create Event...")
    event_name = "Test Event"
    create_event(event_name, "2023-10-27", "10:00", "11:00")
    events = get_events()
    print(f"Event List: {events}")
    assert any(e[1] == event_name for e in events), "Event not created"
    
    # Get IDs
    s_id = [s[0] for s in staff if s[1] == staff_name][0]
    e_id = [e[0] for e in events if e[1] == event_name][0]

    # Test 3: Mark Attendance
    print("Testing Mark Attendance...")
    mark_event_attendance(e_id, [s_id])
    attended = get_event_attendance(e_id)
    print(f"Attended IDs: {attended}")
    assert s_id in attended, "Attendance not marked"

    # Test 4: Report
    print("Testing Report...")
    report = get_full_event_report()
    print(f"Report: {report}")
    assert len(report) > 0, "Report empty"
    
    print("ALL TESTS PASSED")

if __name__ == "__main__":
    test_verification()
