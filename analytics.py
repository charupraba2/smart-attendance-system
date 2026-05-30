import pandas as pd
from datetime import datetime
from database import get_all_past_events, get_all_attendance_flat, get_all_staff

def calculate_staff_insights():
    """
    Analyzes historical data to generate insights for each staff member.
    Returns a DataFrame with cols: [Name, Present, Total Events, Attendance%, Late, Early, Risk Label, Next Event Prob]
    """
    # 1. Get Data
    all_staff = get_all_staff() # [(id, name, dept, desg), ...]
    past_events = get_all_past_events() # [(id, name, date, start, end), ...]
    attendance_records = get_all_attendance_flat() # [(staff_id, name, event_id, in_time, out_time, e_start, e_end, e_date), ...]
    
    total_events_count = len(past_events)
    if total_events_count == 0:
        return pd.DataFrame()

    # Create Dictionary for quick lookup
    staff_stats = {}
    for s in all_staff:
        staff_stats[s[0]] = {
            "Name": s[1],
            "Department": s[2],
            "Present": 0,
            "Late": 0,
            "Early": 0,
            "Total": total_events_count
        }

    # Process Attendance
    for record in attendance_records:
        s_id = record[0]
        in_time_str = record[3]
        out_time_str = record[4]
        e_start_str = record[5]
        e_end_str = record[6]

        if s_id in staff_stats:
            staff_stats[s_id]["Present"] += 1
            
            # Late Check
            # Simple string comparison works for HH:MM:SS if format is consistent
            if in_time_str > e_start_str:
                staff_stats[s_id]["Late"] += 1
            
            # Early Exit Check (if exit time exists)
            # We allow 5 mins buffer maybe? keeping it strict for now.
            if out_time_str and e_end_str and out_time_str < e_end_str:
                 staff_stats[s_id]["Early"] += 1

    # Calculate Derived Metrics
    results = []
    for s_id, stats in staff_stats.items():
        attendance_pct = (stats["Present"] / total_events_count) * 100 if total_events_count > 0 else 0
        
        # Risk Logic
        if attendance_pct < 50:
            risk = "Results: High Risk (Absentee)"
            status_color = "🔴"
        elif attendance_pct < 80:
            risk = "Results: Moderate (Irregular)"
            status_color = "🟡"
        else:
            risk = "Results: Low Risk (Regular)"
            status_color = "🟢"

        # Probability of Next Event (Naive Bayes -ish / Simple Frequency)
        # Prob = Attendance %
        prob = f"{attendance_pct:.1f}%"

        results.append({
            "Staff Name": stats["Name"],
            "Department": stats["Department"],
            "Attendance %": f"{attendance_pct:.1f}%",
            "Present / Total": f"{stats['Present']} / {total_events_count}",
            "Late Arrivals": stats["Late"],
            "Early Exits": stats["Early"],
            "Status": f"{status_color} {risk}",
            "Next Event Prob": prob
        })

    return pd.DataFrame(results)

def get_department_trends():
    """
    Aggregates attendance by department.
    """
    # Re-using logic or separate SQL? 
    # Let's simple aggregation in Python
    df = calculate_staff_insights()
    if df.empty:
        return pd.DataFrame()
    
    # We need raw numbers, so let's parse percentage back or re-calculate.
    # Actually, let's just use the raw 'Attendance %' string and convert to float for aggregating?
    # Better to re-aggregate from source if needed, but for 'Trends' let's just average the Staff % in that dept.
    
    df['Pct_Val'] = df['Attendance %'].str.rstrip('%').astype(float)
    
    dept_trends = df.groupby('Department')['Pct_Val'].mean().reset_index()
    dept_trends.columns = ['Department', 'Avg Attendance %']
    dept_trends['Avg Attendance %'] = dept_trends['Avg Attendance %'].round(1)
    
    return dept_trends

def predict_event_success(event_date_str):
    """
    Predicts turnout based on day of week.
    """
    # 1. Get all past events and their turnout
    past_events = get_all_past_events()
    attendance_records = get_all_attendance_flat()
    
    if not past_events:
        return "N/A (No History)"

    # Map Event ID to Date
    event_dates = {e[0]: e[2] for e in past_events}
    
    # Count attendance per event
    event_counts = {}
    for r in attendance_records:
        eid = r[2]
        event_counts[eid] = event_counts.get(eid, 0) + 1
        
    # Calculate Turnout % per event (assuming fixed staff count? or approximating)
    # Let's mostly care about raw numbers or average count.
    
    # 2. Get Weekday of target date
    try:
        target_date = datetime.strptime(event_date_str, "%Y-%m-%d")
        target_weekday = target_date.weekday() # 0=Mon, 6=Sun
        
        # Filter past events by this weekday
        relevant_turnouts = []
        for eid, date_str in event_dates.items():
            d = datetime.strptime(date_str, "%Y-%m-%d")
            if d.weekday() == target_weekday:
                relevant_turnouts.append(event_counts.get(eid, 0))
        
        if relevant_turnouts:
            avg_turnout = sum(relevant_turnouts) / len(relevant_turnouts)
            return f"Expected Turnout: ~{int(avg_turnout)} Staff (Based on similar days)"
        else:
            return "No historical data for this day of week."
            
    except Exception as e:
        return f"Error: {e}"

def get_overall_stats():
    """
    Returns summary metrics for the dashboard.
    """
    all_staff = get_all_staff()
    past_events = get_all_past_events()
    attendance_records = get_all_attendance_flat()
    
    total_staff = len(all_staff)
    total_events = len(past_events)
    total_records = len(attendance_records)
    
    # Calculate global average attendance
    if total_events > 0 and total_staff > 0:
        avg_attendance = (total_records / (total_staff * total_events)) * 100
    else:
        avg_attendance = 0
        
    return {
        "total_staff": total_staff,
        "total_events": total_events,
        "total_records": total_records,
        "avg_attendance": round(avg_attendance, 1)
    }

def get_attendance_trends():
    """
    Returns date-wise attendance counts.
    """
    records = get_all_attendance_flat()
    if not records:
        return pd.DataFrame(columns=["Date", "Attendance"])
    
    # record: (staff_id, name, event_id, in_time, out_time, e_start, e_end, e_date)
    df = pd.DataFrame(records, columns=["staff_id", "name", "event_id", "in_time", "out_time", "e_start", "e_end", "Date"])
    
    trends = df.groupby("Date").size().reset_index(name="Attendance")
    trends = trends.sort_values("Date")
    return trends

def get_top_staff(limit=5):
    """
    Returns top-performing staff by attendance percentage.
    """
    df = calculate_staff_insights()
    if df.empty:
        return pd.DataFrame()
    
    # Convert 'Attendance %' string back to float for sorting
    df['Attendance_Val'] = df['Attendance %'].str.rstrip('%').astype(float)
    top_staff = df.sort_values(by=['Attendance_Val', 'Late Arrivals'], ascending=[False, True]).head(limit)
    
    return top_staff[["Staff Name", "Department", "Attendance %", "Status"]]
