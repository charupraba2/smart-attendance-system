import sqlite3
import os
from datetime import datetime
import time

DB_PATH = "data/attendance.db"

def create_connection():
    """Create a database connection to the SQLite database specified by DB_PATH."""
    conn = None
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    except Exception as e:
        print(f"Error connecting to database: {e}")
    return conn

def create_table():
    """Create tables if they don't exist."""
    conn = create_connection()
    if conn is not None:
        try:
            c = conn.cursor()
            
            # Staff Table
            c.execute("""CREATE TABLE IF NOT EXISTS staff (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        department TEXT NOT NULL,
                        designation TEXT NOT NULL
                        )""")

            # Events Table
            c.execute("""CREATE TABLE IF NOT EXISTS events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        date TEXT NOT NULL,
                        time TEXT NOT NULL,
                        end_time TEXT,
                        status TEXT DEFAULT 'Upcoming'
                        )""")

            # Event Attendance Table
            c.execute("""CREATE TABLE IF NOT EXISTS event_attendance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_id INTEGER,
                        staff_id INTEGER,
                        check_in_date TEXT,
                        check_in_time TEXT,
                        status TEXT,
                        event_name TEXT,
                        staff_name TEXT,
                        exit_time TEXT,
                        duration TEXT,
                        source TEXT DEFAULT 'Live'
                        )""")

            # Users Table
            c.execute("""CREATE TABLE IF NOT EXISTS users (
                        username TEXT PRIMARY KEY,
                        password TEXT NOT NULL,
                        role TEXT NOT NULL
                        )""")

            # Action Logs Table
            c.execute("""CREATE TABLE IF NOT EXISTS action_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        admin_name TEXT,
                        action TEXT,
                        target TEXT,
                        timestamp TEXT
                        )""")

            conn.commit()
        except Exception as e:
            print(f"Error creating tables: {e}")
        finally:
            conn.close()

# --- Staff Management ---

def add_staff(name, department, designation):
    conn = create_connection()
    if conn:
        try:
            c = conn.cursor()
            c.execute("INSERT INTO staff (name, department, designation) VALUES (?, ?, ?)", 
                      (name, department, designation))
            conn.commit()
        except Exception as e:
            print(f"Error adding staff: {e}")
        finally:
            conn.close()

def get_all_staff():
    conn = create_connection()
    if conn:
        try:
            c = conn.cursor()
            c.execute("SELECT * FROM staff")
            return c.fetchall()
        except Exception as e:
            print(f"Error getting staff: {e}")
            return []
        finally:
            conn.close()

def delete_staff(staff_id):
    conn = create_connection()
    if conn:
        try:
            c = conn.cursor()
            c.execute("DELETE FROM staff WHERE id=?", (staff_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting staff: {e}")
            return False
        finally:
            conn.close()

def delete_staff_safe(staff_id, current_user):
    conn = create_connection()
    if conn:
        try:
            c = conn.cursor()
            # Get staff name for logging
            c.execute("SELECT name FROM staff WHERE id=?", (staff_id,))
            res = c.fetchone()
            name = res[0] if res else "Unknown"
            
            c.execute("DELETE FROM staff WHERE id=?", (staff_id,))
            conn.commit()
            
            log_action(current_user, "DELETE STAFF", f"ID: {staff_id}, Name: {name}")
            return True
        except Exception as e:
            print(f"Error deleting staff safe: {e}")
            return False
        finally:
            conn.close()

# --- Event Management ---

def create_event(name, date, time_str, end_time_str):
    conn = create_connection()
    if conn:
        try:
            c = conn.cursor()
            c.execute("INSERT INTO events (name, date, time, end_time, status) VALUES (?, ?, ?, ?, 'Upcoming')",
                      (name, date, time_str, end_time_str))
            conn.commit()
        except Exception as e:
            print(f"Error creating event: {e}")
        finally:
            conn.close()

def get_events():
    conn = create_connection()
    if conn:
        try:
            c = conn.cursor()
            # Order by date descending, then time
            c.execute("SELECT * FROM events ORDER BY date DESC, time DESC")
            return c.fetchall()
        except Exception as e:
            print(f"Error getting events: {e}")
            return []
        finally:
            conn.close()

def update_event_status(event_id, status):
    conn = create_connection()
    if conn:
        try:
            c = conn.cursor()
            c.execute("UPDATE events SET status=? WHERE id=?", (status, event_id))
            conn.commit()
        except Exception as e:
            print(f"Error updating event status: {e}")
        finally:
            conn.close()

def is_event_active(event_id, date_str, start_time_str, end_time_str, status):
    """
    Checks if an event is currently active based on date and time.
    Returns (is_active, reason)
    """
    try:
        now = datetime.now()
        event_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        # Parse times
        # Handle cases where seconds might be missing
        try:
            start_time = datetime.strptime(start_time_str, "%H:%M:%S").time()
        except ValueError:
            start_time = datetime.strptime(start_time_str, "%H:%M").time()
            
        try:
            end_time = datetime.strptime(end_time_str, "%H:%M:%S").time()
        except ValueError:
             try:
                 end_time = datetime.strptime(end_time_str, "%H:%M").time()
             except:
                 end_time = datetime.strptime("23:59:59", "%H:%M:%S").time() # Default fallback

        # Combine to full datetime
        event_start_dt = datetime.combine(event_date, start_time)
        event_end_dt = datetime.combine(event_date, end_time)
        
        if now < event_start_dt:
            return False, "Event has not started yet (Future)"
        elif now > event_end_dt:
            # Auto-update status to Completed if passed
            if status != 'Completed':
                update_event_status(event_id, 'Completed')
            return False, "Event has ended (Past)"
        else:
            # It's within the time window
            if status == 'Upcoming':
                 update_event_status(event_id, 'Active')
            elif status == 'Completed':
                 return False, "Event manually marked as Completed"
            
            return True, "Active"

    except Exception as e:
        return False, f"Error checking status: {e}"

def delete_event_safe(event_id, current_user):
    conn = create_connection()
    if conn:
        try:
            c = conn.cursor()
            c.execute("SELECT name FROM events WHERE id=?", (event_id,))
            res = c.fetchone()
            name = res[0] if res else "Unknown"

            c.execute("DELETE FROM events WHERE id=?", (event_id,))
            # Also delete attendance records for this event? Maybe keep them for history.
            # Choosing to keep attendance records but maybe link is broken. 
            # Ideally standard foreign keys would handle this but sqlite is loose.
            
            conn.commit()
            log_action(current_user, "DELETE EVENT", f"ID: {event_id}, Name: {name}")
            return True
        except Exception as e:
            print(f"Error deleting event: {e}")
            return False
        finally:
            conn.close()

def update_event_details(event_id, date, start, end, current_user):
    conn = create_connection()
    if conn:
        try:
            c = conn.cursor()
            c.execute("UPDATE events SET date=?, time=?, end_time=? WHERE id=?", 
                      (date, start, end, event_id))
            conn.commit()
            log_action(current_user, "UPDATE EVENT", f"ID: {event_id} date/time updated")
            return True
        except Exception as e:
            print(f"Error updating event: {e}")
            return False
        finally:
            conn.close()

# --- Attendance Logic ---

def mark_event_attendance_face(event_id, staff_name, source="Live"):
    """
    Marks attendance for a staff member at an event.
    If already checked in, updates exit time.
    """
    conn = create_connection()
    if conn:
        try:
            c = conn.cursor()
            
            # 1. Get Staff Details
            c.execute("SELECT id, name, department, designation FROM staff WHERE name=?", (staff_name,))
            staff = c.fetchone()
            if not staff:
                return False, f"Staff '{staff_name}' not found in database."
            
            staff_id, s_name, s_dept, s_desg = staff
            
            # 2. Get Event Name
            c.execute("SELECT name FROM events WHERE id=?", (event_id,))
            event = c.fetchone()
            event_name = event[0] if event else "Unknown Event"

            current_date = datetime.now().strftime("%Y-%m-%d")
            current_time = datetime.now().strftime("%H:%M:%S")

            # 3. Check if already marked
            c.execute("SELECT id, check_in_time FROM event_attendance WHERE event_id=? AND staff_id=?", 
                      (event_id, staff_id))
            existing = c.fetchone()
            
            if existing:
                # Already checked in -> Update Exit Time
                att_id = existing[0]
                check_in_t = existing[1]
                
                # Calculate Duration
                # Simple calculation if in same day
                try:
                    t1 = datetime.strptime(check_in_t, "%H:%M:%S")
                    t2 = datetime.strptime(current_time, "%H:%M:%S")
                    duration_seconds = (t2 - t1).total_seconds()
                    duration_str = str(datetime.utcfromtimestamp(duration_seconds).time())
                except:
                    duration_str = "N/A"

                c.execute("""UPDATE event_attendance 
                             SET exit_time=?, duration=?, status='Present' 
                             WHERE id=?""", 
                             (current_time, duration_str, att_id))
                conn.commit()
                return False, f"Updated exit time for {staff_name}" # False means not a NEW check-in
            else:
                # New Check-in
                c.execute("""INSERT INTO event_attendance 
                             (event_id, staff_id, check_in_date, check_in_time, status, event_name, staff_name, exit_time, duration, source)
                             VALUES (?, ?, ?, ?, 'Present', ?, ?, ?, ?, ?)""",
                             (event_id, staff_id, current_date, current_time, event_name, staff_name, current_time, "00:00:00", source))
                conn.commit()
                return True, f"Checked in {staff_name}" # True means NEW check-in

        except Exception as e:
            print(f"Error marking attendance: {e}")
            return False, f"Error: {e}"
        finally:
            conn.close()

def get_event_report(event_id):
    conn = create_connection()
    if conn:
        try:
            c = conn.cursor()
            # Fetch relevant columns for report
            c.execute("SELECT * FROM event_attendance WHERE event_id=?", (event_id,))
            return c.fetchall()
        except Exception as e:
            print(f"Error getting report: {e}")
            return []
        finally:
            conn.close()

def get_filtered_attendance(search_query=None):
    conn = create_connection()
    if conn:
        try:
            c = conn.cursor()
            
            # Need to JOIN with staff to get latest dept/desg if strictly needed, 
            # but event_attendance already has some cached fields? 
            # No, event_attendance schema has staff_name but not dept/desg.
            # Wait, report in app.py expects: Event, Date, Entry Time, Exit Time, Staff Name, Dept, Desg, Status
            
            query = """
                SELECT 
                    ea.event_name, 
                    ea.check_in_date, 
                    ea.check_in_time, 
                    ea.exit_time, 
                    s.name, 
                    s.department, 
                    s.designation,
                    ea.status
                FROM event_attendance ea
                JOIN staff s ON ea.staff_id = s.id
            """
            
            params = []
            if search_query:
                query += """ WHERE 
                    ea.event_name LIKE ? OR 
                    s.name LIKE ? OR 
                    ea.check_in_date LIKE ? OR
                    s.department LIKE ?
                """
                pattern = f"%{search_query}%"
                params = [pattern, pattern, pattern, pattern]
            
            query += " ORDER BY ea.check_in_date DESC, ea.check_in_time DESC"
            
            c.execute(query, params)
            return c.fetchall()
        except Exception as e:
            print(f"Error filtering attendance: {e}")
            return []
        finally:
            conn.close()

def get_or_create_event_by_details(name, date, start, end, current_user="System"):
    """
    Finds an event by name and date, or creates a new one.
    Returns (event_id, was_created, message)
    """
    conn = create_connection()
    if conn:
        try:
            c = conn.cursor()
            # 1. Search for existing event
            c.execute("SELECT id FROM events WHERE name=? AND date=?", (name, date))
            res = c.fetchone()
            
            if res:
                return res[0], False, "Found existing event."
            
            # 2. Create new event if not found
            # Assuming 'Active' or 'Upcoming' based on time? 
            # For upload, we just create it as 'Upcoming' or 'Completed' depending on logic?
            # Let's default to standard creation
            c.execute("INSERT INTO events (name, date, time, end_time, status) VALUES (?, ?, ?, ?, 'Upcoming')",
                      (name, date, start, end))
            conn.commit()
            new_id = c.lastrowid
            
            log_action(current_user, "CREATE EVENT (UPLOAD)", f"ID: {new_id}, Name: {name}")
            return new_id, True, "Created new event."
            
        except Exception as e:
            print(f"Error get/create event: {e}")
            return None, False, f"Error: {e}"
        finally:
            conn.close()

def mark_media_attendance(event_id, staff_name, source_type):
    """
    Marks attendance from media upload (Photo/Video).
    Only inserts if no record exists for this staff/event.
    """
    conn = create_connection()
    if conn:
        try:
            c = conn.cursor()
            
            # 1. Get Staff Details
            c.execute("SELECT id, name FROM staff WHERE name=?", (staff_name,))
            staff = c.fetchone()
            if not staff:
                return False, f"Staff '{staff_name}' not found."
            
            staff_id, s_name = staff
            
            # 2. Get Event Name
            c.execute("SELECT name FROM events WHERE id=?", (event_id,))
            event = c.fetchone()
            event_name = event[0] if event else "Unknown Event"

            # 3. Check for existing record
            c.execute("SELECT id FROM event_attendance WHERE event_id=? AND staff_id=?", 
                      (event_id, staff_id))
            existing = c.fetchone()
            
            if existing:
                return False, f"Skipped {s_name} (Already Marked)"
            
            # 4. Insert New Record
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Set duration to 0 or N/A as it's a point-in-time check
            c.execute("""INSERT INTO event_attendance 
                         (event_id, staff_id, check_in_date, check_in_time, status, event_name, staff_name, exit_time, duration, source)
                         VALUES (?, ?, ?, ?, 'Present', ?, ?, ?, ?, ?)""",
                         (event_id, staff_id, timestamp.split(' ')[0], timestamp.split(' ')[1], 
                          event_name, s_name, timestamp.split(' ')[1], "00:00:00", source_type))
            conn.commit()
            return True, f"Marked {s_name} (New)"

        except Exception as e:
            print(f"Error media attendance: {e}")
            return False, f"Error: {e}"
        finally:
            conn.close()

# --- User & Logging ---

def verify_user(username, password):
    conn = create_connection()
    if conn:
        try:
            c = conn.cursor()
            c.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
            res = c.fetchone()
            if res:
                return res[0] # Returns role (e.g., 'ADMIN')
            return None
        except Exception as e:
            print(f"Error verifying user: {e}")
            return None
        finally:
            conn.close()

def log_action(admin_name, action, target):
    conn = create_connection()
    if conn:
        try:
            c = conn.cursor()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO action_logs (admin_name, action, target, timestamp) VALUES (?, ?, ?, ?)",
                      (admin_name, action, target, timestamp))
            conn.commit()
        except Exception as e:
            print(f"Error logging action: {e}")
        finally:
            conn.close()

def get_logs():
    conn = create_connection()
    if conn:
        try:
            c = conn.cursor()
            c.execute("SELECT * FROM action_logs ORDER BY timestamp DESC")
            return c.fetchall()
        except Exception as e:
            print(f"Error getting logs: {e}")
            return []
        finally:
            conn.close()

# --- Compatibility Stubs (if referenced elsewhere but not core) ---
def get_event_attendance(event_id):
    # This was referenced in verify_backend.py
    # Returns list of staff_ids who attended
    conn = create_connection()
    if conn:
        try:
            c = conn.cursor()
            c.execute("SELECT staff_id FROM event_attendance WHERE event_id=?", (event_id,))
            return [row[0] for row in c.fetchall()]
        except Exception as e:
            print(f"Error get_event_attendance: {e}")
            return []
        finally:
            conn.close()

def get_full_event_report():
    # Referenced in verify_backend.py
    return get_filtered_attendance()

def mark_event_attendance(event_id, staff_ids):
    # Referenced in verify_backend.py - manual list marking
    # Adapt to use facial logic or direct insert
    conn = create_connection()
    if conn:
        try:
            c = conn.cursor()
            # Loop
            for sid in staff_ids:
                # Get details
                c.execute("SELECT name FROM staff WHERE id=?", (sid,))
                sres = c.fetchone()
                if sres:
                    sname = sres[0]
                    mark_event_attendance_face(event_id, sname)
        except Exception as e:
            print(f"Error mark_event_attendance: {e}")
        finally:
            conn.close()

# --- Analytics Support ---

def get_all_past_events():
    """
    Returns all events that are either Completed or in the past.
    Returns list of tuples: (id, name, date, start_time, end_time)
    """
    conn = create_connection()
    if conn:
        try:
            c = conn.cursor()
            # Logic: status='Completed' OR date < current_date
            # Simple approach: Return all events for now, analytics filters logic somewhat.
            # Analytics expects: [(id, name, date, start, end), ...]
            c.execute("SELECT id, name, date, time, end_time FROM events WHERE status='Completed' OR date < date('now')")
            return c.fetchall()
        except Exception as e:
            print(f"Error getting past events: {e}")
            return []
        finally:
            conn.close()

def get_all_attendance_flat():
    """
    Returns a flat list of all attendance records for analytics.
    Expected columns based on analytics.py:
    (staff_id, name, event_id, in_time, out_time, e_start, e_end, e_date)
    """
    conn = create_connection()
    if conn:
        try:
            c = conn.cursor()
            query = """
                SELECT 
                    ea.staff_id,
                    ea.staff_name,
                    ea.event_id,
                    ea.check_in_time,
                    ea.exit_time,
                    e.time,
                    e.end_time,
                    e.date
                FROM event_attendance ea
                JOIN events e ON ea.event_id = e.id
            """
            c.execute(query)
            return c.fetchall()
        except Exception as e:
            print(f"Error getting flat attendance: {e}")
            return []
        finally:
            conn.close()

