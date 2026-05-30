import streamlit as st
import cv2
import pandas as pd
import time
import os
import numpy as np
import tempfile
from datetime import datetime
from database import (
    create_table, add_staff, get_all_staff, delete_staff,
    create_event, get_events, mark_event_attendance_face, get_event_report,
    update_event_status, is_event_active,
    verify_user, log_action, get_logs, delete_event_safe, delete_staff_safe, update_event_details,
    get_filtered_attendance, get_or_create_event_by_details, mark_media_attendance
)
from analytics import (
    calculate_staff_insights, get_department_trends, predict_event_success,
    get_overall_stats, get_attendance_trends, get_top_staff
)
from utils import load_encodings, recognize_faces
import base64

# Helper for image background/logo
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Page Config
st.set_page_config(page_title="Attendance System", page_icon="📸", layout="wide")

# Load Custom CSS
# Load Custom CSS
def load_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css("style.css")

# Initialize Session State
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'role' not in st.session_state:
    st.session_state.role = None
if 'username' not in st.session_state:
    st.session_state.username = None
    
if 'active_event_id' not in st.session_state:
    st.session_state.active_event_id = None
if 'active_event_name' not in st.session_state:
    st.session_state.active_event_name = None

# --- HEADER LOGIC ---
def render_header():
    # Hide global header on Welcome Page
    if st.session_state.page == 'home':
        return

    logo_file = "images/college_logo.jpg"
    logo_b64 = ""
    if os.path.exists(logo_file):
        logo_b64 = get_base64_of_bin_file(logo_file)
    
    header_html = f"""
    <div class="app-header">
        <div class="header-content">
            <img src="data:image/jpg;base64,{logo_b64}" class="header-logo">
            <p class="header-title">BISHOP HEBER COLLEGE (AUTONOMOUS)</p>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

render_header()
# --------------------

# Database Init
create_table()

# Load Encodings
@st.cache_resource
def get_face_data():
    return load_encodings()

known_encodings, known_names = get_face_data()

# Navigation Functions
def go_home():
    st.session_state.page = 'home'
    st.session_state.active_event_id = None # Reset event when successful

def go_admin():
    st.session_state.page = 'admin_login'

def logout():
    st.session_state.authenticated = False
    st.session_state.role = None
    st.session_state.username = None
    go_home()

# --- PAGES ---

# --- PAGES ---

def show_home():
    # Background Image Logic
    img_file = "images/welcome_bg.png"
    if os.path.exists(img_file):
        bin_str = get_base64_of_bin_file(img_file)
        page_bg_img = f"""
        <style>
        .stApp {{
            background-image: linear-gradient(rgba(15, 23, 42, 0.8), rgba(15, 23, 42, 0.9)), url("data:image/png;base64,{bin_str}") !important;
            background-size: cover !important;
            background-position: center !important;
            background-attachment: fixed !important;
        }}
        </style>
        """
        st.markdown(page_bg_img, unsafe_allow_html=True)
    
    # Modern Landing Layout
    st.markdown("""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 70vh; text-align: center;">
        <h1 style="font-size: 3.5rem; font-weight: 800; background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 1rem;">Attendance System</h1>
        <p style="font-size: 1.2rem; color: #94a3b8; max-width: 600px; margin-bottom: 2.5rem; line-height: 1.6;">
            Secure, efficient, and automated event attendance tracking.<br>
            Powered by advanced face recognition technology.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Centered Login Action
    col1, col2, col3 = st.columns([5, 2, 5])
    with col2:
         if st.button("Start", type="primary", use_container_width=True):
             st.session_state.page = 'admin_login'
             st.rerun()

# ... (existing code)

def show_admin_dashboard():
    role = st.session_state.role
    current_user = st.session_state.username
    
    # Top Navigation Bar
    col_nav1, col_nav2 = st.columns([8, 1])
    with col_nav1:
        # Status Indicator (No Greeting)
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 8px; padding-top: 5px;">
            <span style="height: 10px; width: 10px; background-color: #22c55e; border-radius: 50%; display: inline-block;"></span>
            <span style="color: #94A3B8; font-weight: 500; font-size: 0.9em; text-transform: uppercase; letter-spacing: 1px;">{role}</span>
        </div>
        """, unsafe_allow_html=True)
        
    with col_nav2:
        if st.button("Logout", key="top_logout"):
            logout()
            st.rerun()
    
    st.divider()

def show_attendance():
    if not st.session_state.active_event_id:
        st.error("No active event session. Please start one from Admin Dashboard.")
        if st.button("Go Back"):
            go_home()
            st.rerun()
        return

    # --- STRICT CAMERA ACCESS CHECK (Start) ---
    # 1. Get Event Details
    events = get_events()
    event_details = None
    for e in events:
        if e[0] == st.session_state.active_event_id:
            event_details = e # (id, name, date, time, end_time, status)
            break
            
    if not event_details:
        st.error("Event not found / Invalid Session.")
        st.session_state.active_event_id = None
        time.sleep(2)
        st.rerun()
        return

    # 2. Check Logic BEFORE Camera Init
    e_id, e_name, e_date, e_start, e_end, e_status = event_details
    active, reason = is_event_active(e_id, e_date, e_start, e_end, e_status)

    if not active:
        st.markdown(f"""
        <div style="text-align: center; padding: 50px;">
            <h1 style="color: var(--danger); font-size: 3rem;">🛑</h1>
            <h2 style="color: var(--text-primary);">Camera Access Disabled</h2>
            <p style="color: var(--text-secondary); font-size: 1.2rem; margin-top: 10px;">{reason}</p>
            <hr style="border-color: var(--bg-card-hover); margin: 30px 0;">
        </div>
        """, unsafe_allow_html=True)
        
        st.error(f"Event Status: {reason}")
        
        if st.button("← Return to Dashboard", type="primary"):
            st.session_state.active_event_id = None
            st.session_state.active_event_name = None
            go_home()
            st.rerun()
        return
    # --- STRICT CAMERA ACCESS CHECK (End) ---

    st.markdown(f"<h2 style='text-align: center; margin-bottom: 20px;'>📸 Event Mode: <span class='text-accent'>{st.session_state.active_event_name}</span></h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="stCard">', unsafe_allow_html=True)
        run_camera = st.checkbox("Active Camera", value=True)
        frame_placeholder = st.empty()
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Stop Button styled
        if st.button("⏹ Stop Attendance Session", type="primary", use_container_width=True):
            st.session_state.active_event_id = None
            st.session_state.active_event_name = None
            st.success("Session Ended.")
            time.sleep(1)
            go_home()
            st.rerun()

    with col2:
        st.markdown('<div class="stCard" style="height: 100%;">', unsafe_allow_html=True)
        st.write("### 📝 Live Log")
        status_log = st.container()
        st.markdown('</div>', unsafe_allow_html=True)

    if run_camera:
        # Load existing marked staff for this event to avoid re-processing/DB calls
        records = get_event_report(st.session_state.active_event_id)
        # records items: (Event, CheckInDate, CheckInTime, StaffName, ...)
        marked_names = {r[3] for r in records} if records else set()
        
        video_capture = cv2.VideoCapture(0)
        
        while run_camera and st.session_state.active_event_id:
            # 1. Periodic strict validation (Double Check inside loop)
            # Fetch details again to ensure real-time cutoff
            # OPTIONAL: To save DB calls, we can check just time vs e_end if we trust local time?
            # But specific Requirement: "Event status = LIVE NOW". Status might change in DB.
            # So we should probably keep re-checking or rely on the initial check + local time check.
            # Let's do a lightweight check.
            
            # Simple Time Check
            now = datetime.now()
            # Parse End Time
            try:
                end_dt = datetime.combine(datetime.strptime(e_date, '%Y-%m-%d').date(), datetime.strptime(e_end, '%H:%M:%S').time())
                if now > end_dt:
                     print("Strict Limit Reached") # Console log
                     st.error("🛑 Event Time Ended. Camera Stopping.")
                     st.session_state.active_event_id = None
                     time.sleep(2)
                     st.rerun()
                     break
            except:
                pass

            ret, frame = video_capture.read()
            if not ret:
                break
            
            # Recognition
            frame, names = recognize_faces(frame, known_encodings, known_names)
            
            for name in names:
                if name != "Unknown":
                    # Update Logic: Only update DB if last update was > 30s ago (or never)
                    current_ts = time.time()
                    last_update_ts = st.session_state.get(f"last_update_{name}", 0)
                    
                    if (current_ts - last_update_ts) > 30: # 30 seconds throttle
                        success, msg = mark_event_attendance_face(st.session_state.active_event_id, name)
                        st.session_state[f"last_update_{name}"] = current_ts
                        
                        if success: # First time check-in
                            marked_names.add(name)
                            st.toast(f"✅ {msg}", icon='🎉')
                            with status_log:
                                st.success(msg)
                        else: # Update Exit Time
                            # Optional: Log update
                            pass


            # Display
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Overlay timer
            cv2.putText(frame, f"Event Ends: {e_end}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            frame_placeholder.image(frame, channels="RGB", use_container_width=True)
            time.sleep(0.01)
            
        video_capture.release()

def show_admin_login():
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("""
        <div class="stCard" style="text-align: center;">
            <h2 style="margin-bottom: 20px;">Staff & Admin Portal</h2>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)
            
            if submitted:
                role = verify_user(username, password)
                if role:
                    st.session_state.authenticated = True
                    st.session_state.role = role
                    st.session_state.username = username
                    st.session_state.page = 'admin_dashboard'
                    st.toast(f"Welcome back, {username}!", icon='👋')
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        
        if st.button("← Back to Home", type="secondary"):
            go_home()
            st.rerun()

@st.dialog("Confirm Deletion")
def confirm_delete_event(event_id, current_user):
    st.warning("Are you sure you want to delete this event? This action cannot be undone.")
    if st.button("Yes, Delete Event", type="primary"):
        success = delete_event_safe(event_id, current_user)
        if success:
            st.success("Event Deleted.")
            st.rerun()
        else:
            st.error("Failed to delete.")

@st.dialog("Confirm Staff Deletion")
def confirm_delete_staff(staff_id, current_user):
    st.warning("Are you sure you want to delete this staff member?")
    if st.button("Yes, Delete Staff", type="primary"):
        success = delete_staff_safe(staff_id, current_user)
        if success:
            st.success("Staff Deleted.")
            st.rerun()
        else:
            st.error("Failed to delete.")
            
@st.dialog("Edit Event")
def edit_event_dialog(e_id, old_date, old_start, old_end, current_user):
    with st.form(f"edit_event_{e_id}"):
        n_date = st.date_input("Event Date", value=datetime.strptime(old_date, '%Y-%m-%d'))
        n_start = st.time_input("Start Time", value=datetime.strptime(old_start, '%H:%M:%S').time())
        n_end_val = datetime.strptime(old_end, '%H:%M:%S').time() if old_end else datetime.strptime("18:00:00", '%H:%M:%S').time()
        n_end = st.time_input("End Time", value=n_end_val)
        
        if st.form_submit_button("Update Event"):
            update_event_details(e_id, str(n_date), str(n_start), str(n_end), current_user)
            st.success("Event Updated")
            st.rerun()

            st.rerun()

def show_media_upload_module(current_user):
    st.subheader("📷 Media Upload Face Recognition")
    st.info("Upload Photos or Videos to detect faces and mark attendance offline.")
    
    # 1. Event Details Form
    with st.container(border=True):
        st.write("#### 1. Event Details")
        c1, c2 = st.columns(2)
        with c1:
            u_event_name = st.text_input("Event Name", placeholder="e.g. Annual Day 2025")
            u_event_date = st.date_input("Date", key="u_date")
        with c2:
            u_start_time = st.time_input("Start Time", key="u_start")
            u_end_time = st.time_input("End Time", key="u_end")
            
    # 2. Upload Section
    with st.container(border=True):
        st.write("#### 2. Upload Media")
        uploaded_file = st.file_uploader("Choose a Photo or Video", type=['jpg', 'jpeg', 'png', 'mp4', 'mov', 'avi'])
        
        if uploaded_file and u_event_name:
            st.divider()
            if st.button("🚀 Process Media & Mark Attendance", type="primary"):
                with st.status("Processing...", expanded=True) as status:
                    # A. Resolve Event
                    status.write("Checking Event Details...")
                    e_id, created, msg = get_or_create_event_by_details(
                        u_event_name, str(u_event_date), str(u_start_time), str(u_end_time), current_user
                    )
                    
                    if not e_id:
                        status.update(label="Error resolving event.", state="error")
                        st.error(msg)
                        return

                    if created:
                        status.write(f"Created new event: {u_event_name}")
                    else:
                        status.write(f"Using existing event: {u_event_name}")
                    
                    # B. Process Media
                    detected_names = set()
                    file_type = uploaded_file.type.split('/')[0] # 'image' or 'video'
                    
                    if file_type == 'image':
                        status.write("Analyzing Image...")
                        # Convert to opencv fmt
                        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
                        frame = cv2.imdecode(file_bytes, 1)
                        
                        # Recognize
                        _, names = recognize_faces(frame, known_encodings, known_names)
                        for n in names:
                            if n != "Unknown":
                                detected_names.add(n)
                                
                    elif file_type == 'video':
                        status.write("Analyzing Video (this may take a moment)...")
                        # Save temp file
                        tfile = tempfile.NamedTemporaryFile(delete=False) 
                        tfile.write(uploaded_file.read())
                        
                        vf = cv2.VideoCapture(tfile.name)
                        
                        frame_count = 0
                        while vf.isOpened():
                            ret, frame = vf.read()
                            if not ret:
                                break
                            
                            # Process every 30th frame for speed
                            if frame_count % 30 == 0:
                                _, names = recognize_faces(frame, known_encodings, known_names)
                                for n in names:
                                    if n != "Unknown":
                                        detected_names.add(n)
                            frame_count += 1
                        
                        vf.release()
                        tfile.close() 
                        try:
                            os.remove(tfile.name)
                        except:
                            pass
                    
                    # C. Store Results
                    status.write("Updating Database...")
                    new_count = 0
                    skip_count = 0
                    
                    results_log = []
                    
                    for name in detected_names:
                        success, log_msg = mark_media_attendance(e_id, name, "Photo" if file_type == 'image' else "Video")
                        if success:
                            new_count += 1
                            results_log.append(f"✅ {name}")
                        else:
                            skip_count += 1
                            results_log.append(f"⏩ {name} (Skipped)")
                            
                    status.update(label="Processing Complete!", state="complete", expanded=False)
                    
                    # Summary
                    st.success(f"Processing Done! Found {len(detected_names)} identifiable faces.")
                    c_res1, c_res2 = st.columns(2)
                    with c_res1:
                        st.metric("New Records Added", new_count)
                    with c_res2:
                        st.metric("Skipped (Existing)", skip_count)
                        
                    with st.expander("Detailed Results", expanded=True):
                        for log in results_log:
                            st.write(log)

def show_mobile_camera_module(current_user):
    st.subheader("📱 Mobile Phone Camera Attendance")
    st.info("Use your mobile phone camera as a live video source for attendance. Connect phone and system to the same Wi-Fi.")

    # 1. Event Details
    with st.container(border=True):
        st.write("#### 1. Event Details")
        c1, c2 = st.columns(2)
        with c1:
            m_event_name = st.text_input("Event Name", key="m_event_name", placeholder="e.g. Conference 2025")
            m_event_date = st.date_input("Date", key="m_event_date")
        with c2:
            m_start_time = st.time_input("Start Time", key="m_start_time")
            m_end_time = st.time_input("End Time", key="m_end_time")

    # 2. Camera Connection
    with st.container(border=True):
        st.write("#### 2. Camera Connection")
        camera_url = st.text_input("Mobile Camera Streaming URL", placeholder="http://192.168.x.x:8080/video")
        
        col_start, col_status = st.columns([1, 2])
        with col_start:
            start_cam = st.toggle("Start Camera", key="m_start_cam")
            
    # 3. Live Feed & Recognition
    if start_cam and camera_url and m_event_name:
        
        # A. Resolve Event
        e_id, created, msg = get_or_create_event_by_details(
            m_event_name, str(m_event_date), str(m_start_time), str(m_end_time), current_user
        )
        
        if not e_id:
            st.error(msg)
            return

        # B. Check Status & Time Validity (STRICT)
        # Fetch full event details to check status
        events = get_events()
        event_info = None
        for e in events:
            if e[0] == e_id:
                event_info = e
                break
        
        if event_info:
             # Unpack: id, name, date, start, end, status
             active, reason = is_event_active(event_info[0], event_info[2], event_info[3], event_info[4], event_info[5])
             
             if not active:
                 st.error(f"🛑 Camera Access Blocked: {reason}")
                 return
        else:
             st.error("Event not found.")
             return

        st.success(f"✅ Connected to Active Event: {m_event_name}")

        # C. Stream
        col_vid, col_log = st.columns([2, 1])
        
        with col_vid:
            st.write("**Live Mobile Feed**")
            frame_placeholder = st.empty()
            
        with col_log:
            st.write("**Attendance Log**")
            log_container = st.container(height=300)
            
        # Video Capture
        cap = cv2.VideoCapture(camera_url)
        
        if not cap.isOpened():
            st.error("❌ Could not connect to mobile camera. Check URL and Wi-Fi connection.")
        else:
            stop_button = st.button("Stop Camera")
            if stop_button:
                start_cam = False
                st.rerun()

            while cap.isOpened() and not stop_button:
                ret, frame = cap.read()
                if not ret:
                    st.error("Failed to read frame.")
                    break
                
                # Recognition
                # Resize for speed?
                # frame_small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
                # rgb_small = cv2.cvtColor(frame_small, cv2.COLOR_BGR2RGB)
                
                frame, names = recognize_faces(frame, known_encodings, known_names)
                
                for name in names:
                    if name != "Unknown":
                        # Throttle updates
                        current_ts = time.time()
                        last_upd = st.session_state.get(f"mob_last_{name}", 0)
                        
                        if (current_ts - last_upd) > 10: # Faster feedback for mobile
                             success, att_msg = mark_event_attendance_face(e_id, name, source="Mobile Camera")
                             st.session_state[f"mob_last_{name}"] = current_ts
                             
                             if success:
                                 with log_container:
                                     st.success(f"{att_msg}")
        
                # Display
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_placeholder.image(frame, channels="RGB", use_container_width=True)
                
                time.sleep(0.01) # Small delay
                
            cap.release()

def show_dashboard():
    st.subheader("📈 Interactive Attendance Dashboard")
    
    stats = get_overall_stats()
    
    # 1. KPI Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="stMetricCard">
            <div class="metric-label">Total Staff</div>
            <div class="metric-value">{stats["total_staff"]}</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="stMetricCard">
            <div class="metric-label">Total Events</div>
            <div class="metric-value">{stats["total_events"]}</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="stMetricCard">
            <div class="metric-label">Total Records</div>
            <div class="metric-value">{stats["total_records"]}</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="stMetricCard">
            <div class="metric-label">Avg Attendance</div>
            <div class="metric-value">{stats["avg_attendance"]}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # 2. Charts Row
    c1, c2 = st.columns(2)
    
    with c1:
        st.write("#### 📅 Attendance Trends")
        trends_df = get_attendance_trends()
        if not trends_df.empty:
            st.line_chart(trends_df.set_index("Date"))
        else:
            st.info("No trend data available yet.")
            
    with c2:
        st.write("#### 🏢 Department Distribution")
        dept_trends = get_department_trends()
        if not dept_trends.empty:
            st.bar_chart(dept_trends.set_index("Department"))
        else:
            st.info("No department data available yet.")
            
    st.divider()
    
    # 3. Tables Row
    t1, t2 = st.columns([2, 1])
    
    with t1:
        st.write("#### 🏆 Top Performing Staff")
        top_staff = get_top_staff()
        if not top_staff.empty:
            st.dataframe(top_staff, use_container_width=True, hide_index=True)
        else:
            st.info("No staff data available.")
            
    with t2:
        st.write("#### 💡 Quick Insights")
        if stats["avg_attendance"] > 80:
             st.success("Overall attendance is excellent! 🎉")
        elif stats["avg_attendance"] > 50:
             st.warning("Attendance is moderate. Consider reviewing schedules.")
        else:
             st.error("Low attendance detected. High risk of absenteeism.")
        
        # Predicted success for next common day
        st.write("**Next Prediction**")
        prediction = predict_event_success(datetime.today().strftime('%Y-%m-%d'))
        st.info(prediction)

def show_admin_dashboard():
    role = st.session_state.role
    current_user = st.session_state.username
    
    # Top Navigation Bar
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0; margin-bottom: 20px; border-bottom: 1px solid var(--bg-card-hover);">
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="height: 35px; width: 35px; background: var(--accent-primary); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
                {role[0]}
            </div>
            <div>
                <div style="font-weight: 600; font-size: 0.9rem;">{current_user}</div>
                <div style="font-size: 0.75rem; color: var(--text-secondary);">{role}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col_logout = st.columns([8, 1])[1]
    with col_logout:
        if st.button("Logout", key="top_logout", type="secondary"):
             logout()
             st.rerun()

             st.rerun()

    
    tabs = ["📈 Dashboard", "👥 Manage Staff", "📅 Events & Attendance", "📊 Event Reports"]
    # Add new module tab
    tabs.append("📷 Media Upload & Recognition")
    tabs.append("📱 Mobile Camera")
    
    if role == 'ADMIN':
        tabs.append("🔮 AI Predictions")
        tabs.append("🛡️ System Logs")
        
    active_tab = st.tabs(tabs)
    
    # --- TAB: Dashboard ---
    with active_tab[0]:
        show_dashboard()

    # --- TAB: Media Upload ---
    # We'll use the index dynamically based on role, but since we just append, 
    # it's: 0=Dash, 1=Staff, 2=Events, 3=Reports, 4=Media, 5=Mobile, 6=AI, 7=Logs if ADMIN
    
    with active_tab[4]:
        show_media_upload_module(current_user)

    # --- TAB: Mobile Camera ---
    with active_tab[5]:
        show_mobile_camera_module(current_user)

    # --- TAB: AI Predictions (Inserted before Logs) ---
    if role == 'ADMIN':
        # AI is now at index 6
        with active_tab[6]:
            st.subheader("🔮 Attendance Insights & Predictions")
            st.info("AI-driven insights based on historical attendance patterns.")
            
            # 1. High Level Metrics
            insights_df = calculate_staff_insights()
            dept_trends = get_department_trends()
            
            if not insights_df.empty:
                avg_attendance = insights_df["Attendance %"].str.rstrip('%').astype(float).mean()
                at_risk_count = insights_df[insights_df["Status"].str.contains("High Risk")].shape[0]
                
                # Metric Cards
                m1, m2, m3 = st.columns(3)
                with m1:
                    st.markdown(f"""
                    <div class="stMetricCard">
                        <div class="metric-label">Avg Attendance</div>
                        <div class="metric-value">{avg_attendance:.1f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                with m2:
                    st.markdown(f"""
                    <div class="stMetricCard">
                        <div class="metric-label">Staff At Risk</div>
                        <div class="metric-value" style="color: var(--danger);">{at_risk_count}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Top Dept
                with m3:
                    if not dept_trends.empty:
                        top_dept = dept_trends.loc[dept_trends['Avg Attendance %'].idxmax()]
                        st.markdown(f"""
                        <div class="stMetricCard">
                            <div class="metric-label">Top Department</div>
                            <div class="metric-value" style="font-size: 1.4rem;">{top_dept['Department']}</div>
                            <div style="font-size: 0.8rem; color: var(--success);">{top_dept['Avg Attendance %']}%</div>
                        </div>
                        """, unsafe_allow_html=True)
                
                st.divider()
                
                # 2. Charts & Trends
                c1, c2 = st.columns(2)
                with c1:
                    st.write("#### Department Wise Trends")
                    if not dept_trends.empty:
                        st.bar_chart(dept_trends.set_index("Department"))
                    else:
                        st.info("Not enough data.")
                        
                with c2:
                    st.write("#### Event Success Prediction")
                    # Simple date picker to predict
                    pred_date = st.date_input("Select Event Date", min_value=datetime.today())
                    if pred_date:
                        prediction = predict_event_success(str(pred_date))
                        st.success(f"📅 **Prediction for {pred_date}:**\n\n{prediction}")

                st.divider()

                # 3. Staff Insights Table
                st.write("#### 🕵️ Staff Attendance Risk Analysis")
                
                # Styling Status
                def highlight_status(val):
                    color = 'green'
                    if 'High Risk' in val: color = 'red'
                    elif 'Moderate' in val: color = 'orange'
                    return f'color: {color}; font-weight: bold'

                st.dataframe(insights_df.style.map(highlight_status, subset=['Status']), use_container_width=True)
                
            else:
                st.warning("Not enough historical data to generate predictions.")
            

    # --- TAB: Staff ---
    with active_tab[1]:
        st.subheader("Manage Staff Members")
        
        # 1. Search Bar (Mandatory)
        search_query = st.text_input("🔍 Search Staff", placeholder="Search by Name, ID, or Department...", label_visibility="collapsed")
        
        # 2. Add Staff (Collapsed to keep UI clean)
        # Only ADMIN can add staff
        if role == 'ADMIN':
            with st.expander("➕ Add New Staff Member", expanded=False):
                with st.form("add_staff_form"):
                    c1, c2, c3 = st.columns(3)
                    with c1: s_name = st.text_input("Name")
                    with c2: s_dept = st.text_input("Department")
                    with c3: s_desg = st.text_input("Designation")
                    
                    if st.form_submit_button("Add Staff Record", type="primary"):
                        if s_name and s_dept:
                            add_staff(s_name, s_dept, s_desg)
                            st.success(f"Added {s_name} successfully!")
                            st.rerun()
                        else:
                            st.warning("Name and Department are required.")
        
        st.divider()
        
        # 3. Staff List (Table View Only)
        staff_data = get_all_staff()
        
        # Filter Logic
        if search_query:
            query = search_query.lower()
            staff_data = [s for s in staff_data if query in str(s[1]).lower() or query in str(s[0]).lower() or query in str(s[2]).lower()]

        # Table Header
        st.markdown("""
        <div class="stTableHeader">
            <div style="display: flex; justify-content: space-between;">
                <div style="width: 5%;">SL</div>
                <div style="width: 10%;">ID</div>
                <div style="width: 25%;">NAME</div>
                <div style="width: 25%;">DEPT</div>
                <div style="width: 15%;">ROLE</div>
                <div style="width: 10%;">STATUS</div>
                <div style="width: 10%; text-align: right;">ACTIONS</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if staff_data:
            for idx, s in enumerate(staff_data, 1):
                # Unpack
                sid = s[0]
                sname = s[1]
                sdept = s[2]
                sdesg = s[3]
                
                # Determine Status
                status_badge = "badge-success"
                status_text = "Active"
                
                # Table Row
                with st.container():
                     # Adjusted widths to match header: 5, 10, 30->25, 25, 20->15, 10, 15->10
                     # Total: 5+10+25+25+15+10+10 = 100%
                     col_sl, col_id, col_name, col_dept, col_role, col_stat, col_act = st.columns([0.5, 1, 2.5, 2.5, 1.5, 1, 1])
                     
                     with col_sl: st.write(f"**{idx}**")
                     with col_id: st.write(f"<span style='color:var(--text-secondary); font-size:0.8rem;'>{sid}</span>", unsafe_allow_html=True)
                     with col_name: st.write(sname)
                     with col_dept: st.write(sdept)
                     with col_role: 
                         badge_cls = "badge-info" if "Admin" in sdesg else "badge-neutral"
                         st.markdown(f"<span class='stBadge {badge_cls}'>{sdesg}</span>", unsafe_allow_html=True)
                     with col_stat:
                         st.markdown(f"<span class='stBadge {status_badge}'>{status_text}</span>", unsafe_allow_html=True)
                     
                     with col_act:
                         if role == 'ADMIN':
                             b_edit, b_del = st.columns(2)
                             with b_edit:
                                 st.button("✏️", key=f"ed_{sid}", help="Edit")
                             with b_del:
                                 if st.button("🗑", key=f"del_{sid}", help="Delete", type="primary"):
                                     confirm_delete_staff(sid, current_user)
                                     
                     st.markdown("<hr style='margin: 0; border-color: var(--bg-card-hover);'>", unsafe_allow_html=True)

        else:
             st.info("No staff records found.")

    # --- TAB: Events & Attendance ---
    with active_tab[2]:
        st.subheader("Manage Events")
        
        events_data = get_events()
        
        # Section A: Create Event (ADMIN ONLY)
        if role == 'ADMIN':
            # Dialog Logic: Check for newly created event
            if 'new_event_created' in st.session_state:
                new_event_name = st.session_state.new_event_created
                # Find ID
                new_event_id = None
                new_event_date = None
                new_event_start = None
                new_event_end = None
                new_event_status = None
                
                for e in events_data:
                    if e[1] == new_event_name:
                        new_event_id = e[0]
                        new_event_date = e[2]
                        new_event_start = e[3]
                        new_event_end = e[4]
                        new_event_status = e[5]
                        break
                
                with st.container(border=True):
                    st.markdown(f"### ✅ Event '{new_event_name}' created successfully.")
                    st.markdown("#### Start face attendance now?")
                    
                    col_yes, col_no = st.columns(2)
                    if col_yes.button("YES", type="primary", use_container_width=True):
                        # STRICT VALIDATION
                        active, reason = is_event_active(new_event_id, new_event_date, new_event_start, new_event_end, new_event_status)
                        if active:
                            if new_event_id:
                                st.session_state.active_event_id = new_event_id
                                st.session_state.active_event_name = new_event_name
                                del st.session_state.new_event_created
                                st.session_state.page = 'attendance'
                                st.rerun()
                        else:
                            st.error(f"Cannot start yet: {reason}")
                    
                    if col_no.button("NO", use_container_width=True):
                        del st.session_state.new_event_created
                        st.rerun()

            else:
                # Create Event Form Card
                st.markdown('<div class="stCard">', unsafe_allow_html=True)
                st.write("#### 🗓️ Schedule New Event")
                with st.form("create_event_form"):
                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        e_name = st.text_input("Event Name")
                        e_date = st.date_input("Event Date")
                    with col_e2:
                        e_start_time = st.time_input("Start Time")
                        e_end_time = st.time_input("End Time")
                    
                    if st.form_submit_button("Create Event", type="primary"):
                        if e_name:
                            if e_end_time <= e_start_time:
                                st.error("End Time must be after Start Time")
                            else:
                                create_event(e_name, str(e_date), str(e_start_time), str(e_end_time))
                                st.session_state.new_event_created = e_name
                                st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        st.divider()
        
        # Section B: Event List
        st.write("#### 📅 Scheduled Events")
        # Table Header
        st.markdown("""
        <div class="stTableHeader">
            <div style="display: flex; justify-content: space-between;">
                <div style="width: 5%;">SL</div>
                <div style="width: 25%;">EVENT</div>
                <div style="width: 15%;">DATE</div>
                <div style="width: 20%;">TIME</div>
                <div style="width: 15%;">STATUS</div>
                <div style="width: 20%; text-align: right;">ACTIONS</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if events_data:
            for idx, event in enumerate(events_data, 1):
                # Unpack
                if len(event) == 6:
                     eid, ename, edate, etime, e_end, estatus = event
                else:
                     eid, ename, edate, etime = event[:4]
                     e_end = "N/A"
                     estatus = "Unknown"

                # Status Logic Visuals
                if estatus == 'Active':
                    badge_color = "badge-success"
                    display_status = "Live Now"
                elif estatus == 'Completed':
                    badge_color = "badge-danger"
                    display_status = "Completed"
                else:
                    badge_color = "badge-info"
                    display_status = "Upcoming"

                # Table Row using Columns
                with st.container():
                    # Adjusted Widths: 5, 25, 15, 20, 15, 20
                    c_sl, c_ev, c_date, c_time, c_stat, c_acts = st.columns([0.5, 2.5, 1.5, 2, 1.5, 2])
                    
                    with c_sl: st.write(f"**{idx}**")
                    with c_ev: st.write(f"**{ename}**")
                    with c_date: st.write(edate)
                    with c_time: st.write(f"{etime} - {e_end}")
                    with c_stat: st.markdown(f"<span class='stBadge {badge_color}'>{display_status}</span>", unsafe_allow_html=True)
                    
                    with c_acts:
                         if role == 'ADMIN':
                             b1, b2, b3 = st.columns([1.5, 1, 1])
                             
                             # 1. Launch (Only if Active)
                             with b1:
                                 if display_status == "Live Now":
                                     if st.button("🚀", key=f"tbl_launch_{eid}", help="Launch Attendance", type="primary"):
                                          active, reason = is_event_active(eid, edate, etime, e_end, estatus)
                                          if active:
                                              st.session_state.active_event_id = eid
                                              st.session_state.active_event_name = ename
                                              st.session_state.page = 'attendance'
                                              st.rerun()
                                          else:
                                              st.error(reason)
                                 elif display_status == "Upcoming":
                                     st.button("🚀", key=f"dis_tbl_{eid}", disabled=True)
                             
                             # 2. Edit (Not Completed)
                             with b2:
                                 if display_status != "Completed":
                                     if st.button("✏️", key=f"tbl_edit_{eid}", help="Edit Event"):
                                          edit_event_dialog(eid, edate, etime, e_end, current_user)
                             
                             # 3. Delete (Always)
                             with b3:
                                 if st.button("🗑", key=f"tbl_del_{eid}", help="Delete Event"):
                                      confirm_delete_event(eid, current_user)
                    
                    st.markdown("<hr style='margin: 0; border-color: var(--bg-card-hover);'>", unsafe_allow_html=True)

        else:
             st.info("No events scheduled.")

    # --- TAB: Reports ---
    with active_tab[3]:
        st.subheader("Event Attendance Reports")
        
        st.markdown('<div class="stCard">', unsafe_allow_html=True)
        # Search & Filter UI
        c_search, c_down = st.columns([3, 1])
        with c_search:
            search_term = st.text_input("🔍 Search Reports", placeholder="Filter by Event, Staff, Date...", label_visibility="collapsed")
        
        if search_term:
             report_data = get_filtered_attendance(search_query=search_term)
        else:
             report_data = get_filtered_attendance() # Get all (or default latest)

        if report_data:
            # Columns: Event, Check-In Date, Check-In Time, Exit Time, Staff Name, Dept, Desg, Status
            report_df = pd.DataFrame(report_data, columns=["Event", "Date", "Entry Time", "Exit Time", "Staff Name", "Department", "Designation", "Status"])
            
            # Calculate Duration
            def calc_duration(row):
                try:
                    fmt = '%H:%M:%S'
                    t1 = datetime.strptime(row['Entry Time'], fmt)
                    t2 = datetime.strptime(row['Exit Time'], fmt)
                    diff = t2 - t1
                    return str(diff)
                except:
                    return "N/A"

            report_df['Duration'] = report_df.apply(calc_duration, axis=1)
            
            # Reorder
            report_df = report_df[["Date", "Event", "Staff Name", "Entry Time", "Exit Time", "Duration", "Status", "Department", "Designation"]]
            
            report_df.index = report_df.index + 1
            st.dataframe(report_df, use_container_width=True)
            
            csv_report = report_df.to_csv(index=False).encode('utf-8')
            with c_down:
                st.download_button("📥 Download CSV", csv_report, "attendance_report.csv", "text/csv", type="primary", use_container_width=True)
        else:
            st.info("No records found matching criteria.")
        
        st.markdown('</div>', unsafe_allow_html=True)
            
    # --- TAB: Logs (ADMIN ONLY) ---
    if role == 'ADMIN':
        with active_tab[7]:
            st.subheader("🛡️ System Audit Logs")
            st.markdown('<div class="stCard">', unsafe_allow_html=True)
            logs = get_logs()
            if logs:
                log_df = pd.DataFrame(logs, columns=["ID", "Admin", "Action", "Target", "Timestamp"])
                log_df.index = log_df.index + 1
                st.dataframe(log_df, use_container_width=True)
            else:
                st.info("No logs found.")
            st.markdown('</div>', unsafe_allow_html=True)

# Router
if st.session_state.page == 'home':
    show_home()
elif st.session_state.page == 'attendance':
    show_attendance()
elif st.session_state.page == 'admin_login':
    show_admin_login()
elif st.session_state.page == 'admin_dashboard':
    if st.session_state.authenticated:
        show_admin_dashboard()
    else:
        go_admin()
        st.rerun()
