# frontend/dashboard.py
import streamlit as st
import json
import urllib.request
import urllib.error
from datetime import date, datetime

def run_teacher_portal(on_exit):
    # Note: st.set_page_config is handled in main_portal.py

    BACKEND_URL = "http://127.0.0.1:5000"

    # ---------------- SESSION ----------------
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "teacher_id" not in st.session_state:
        st.session_state.teacher_id = None

    # ---------------- API HELPERS ----------------
    def api_post(path, payload):
        req = urllib.request.Request(
            f"{BACKEND_URL}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read().decode("utf-8"))

    def api_get(path):
        with urllib.request.urlopen(f"{BACKEND_URL}{path}") as r:
            try:
                return json.loads(r.read().decode("utf-8"))
            except:
                return []

    # ---------------- LOGOUT HELPER ----------------
    def do_logout_to_common():
        st.session_state.logged_in = False
        st.session_state.teacher_id = None
        on_exit()
        st.rerun()

    # ---------------- LOGIN ----------------
    if not st.session_state.logged_in:
        st.markdown("<br><br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div style="background-color: white; padding: 2rem; border-radius: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #e2e8f0;">
                <h2 style="text-align: center; color: #0f172a; border-bottom: none; margin-bottom: 1rem;">Teacher Login</h2>
                <p style="text-align: center; color: #64748b; margin-bottom: 0;">Please sign in to continue</p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            
            teacher_id = st.text_input("Teacher ID")
            password = st.text_input("Password", type="password")

            if st.button("Sign In", use_container_width=True):
                if teacher_id.strip() == "" or password.strip() == "":
                    st.error("Please enter Teacher ID and Password.")
                    st.stop()

                try:
                    resp = api_post(
                        "/teacher/login",
                        {
                            "teacher_id": teacher_id.strip(),
                            "password": password
                        }
                    )
                    st.session_state.logged_in = True
                    st.session_state.teacher_id = resp.get("teacher_id")
                    st.rerun()

                except urllib.error.HTTPError as e:
                    st.error(f"Login failed (HTTP {e.code})")
                except Exception as e:
                    st.error("Backend not reachable.")
                    st.code(str(e))

            st.markdown("---")
            if st.button("Back to Home", key="back_home_login"):
                do_logout_to_common()

        st.stop()

    # ---------------- DASHBOARD ----------------
    try:
        context = api_get(f"/attendance/current-period/{st.session_state.teacher_id}")
    except Exception as e:
        context = {
            "active": False,
            "message": "Backend not reachable",
            "error": str(e)
        }

    # Header with Logout
    head_c1, head_c2 = st.columns([3, 1])
    with head_c1:
        st.title("Teacher Dashboard")
    with head_c2:
        if st.button("Sign Out", key="top_logout"):
            do_logout_to_common()

    # No active period case
    if not context.get("active"):
        st.info(context.get("message", "No active period right now."))
        if context.get("error"):
            st.code(context["error"])
        st.stop()

    # ---------------- INFO METRICS ----------------
    st.subheader("Active Session")
    
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Teacher", context.get("teacher_name", "Unknown"))
    with m2:
        st.metric("Time", f"{context['period_start']} - {context['period_end']}")
    with m3:
        st.metric("Edit Deadline", context['edit_deadline'])
    with m4:
        st.metric("Status", "Active")

    st.markdown("---")

    # ---------------- EDIT DEADLINE CHECK ----------------
    now_t = datetime.now().time()
    deadline_t = datetime.strptime(context["edit_deadline"], "%H:%M").time()
    edit_allowed = now_t <= deadline_t

    if not edit_allowed:
        st.warning(f"Attendance editing closed at {context['edit_deadline']}.")
    else:
        st.success(f"Attendance corrections allowed until {context['edit_deadline']}.")

    # ---------------- TABS FOR FUNCTIONALITY ----------------
    tab1, tab2, tab3, tab4 = st.tabs(["Manual Correction", "Analytics", "Defaulters", "Semester History"])

    # --- TAB 1: MANUAL CORRECTION ---
    with tab1:
        st.subheader("Update Student Attendance")
        
        with st.form("correction_form"):
            c_col1, c_col2, c_col3 = st.columns(3)
            with c_col1:
                student_id = st.text_input("Student ID")
            with c_col2:
                attendance_date = st.date_input("Date", value=date.today())
            with c_col3:
                new_status = st.selectbox("Status", ["Present", "Late", "Absent"])
            
            submit = st.form_submit_button("Submit Correction", disabled=not edit_allowed)

        if submit:
            if not edit_allowed:
                 st.error("Time limit exceeded for edits.")
            elif student_id.strip() == "":
                st.error("Student ID required.")
            else:
                payload = {
                    "teacher_id": st.session_state.teacher_id,
                    "student_id": student_id.strip(),
                    "date": str(attendance_date),
                    "status": new_status
                }
                try:
                    api_post("/attendance/edit", payload)
                    st.success(f"Updated {student_id} to {new_status}")
                except Exception as e:
                     st.error(f"Update failed: {e}")

    # --- TAB 2: ANALYTICS ---
    with tab2:
        st.subheader("Class Attendance Summary")
        if st.checkbox("Load Analytics Data"):
            try:
                data = api_get("/attendance/analytics")
                if data:
                    st.dataframe(data, use_container_width=True)
                else:
                    st.info("No data available.")
            except Exception as e:
                st.error(f"Error: {e}")

    # --- TAB 3: DEFAULTERS ---
    with tab3:
        st.subheader("Defaulters List")
        if st.checkbox("Show Defaulters"):
            try:
                data = api_get("/attendance/defaulters")
                if data:
                    st.dataframe(data, use_container_width=True)
                else:
                    st.success("No defaulters found.")
            except Exception as e:
                st.error(f"Error: {e}")

    # --- TAB 4: SEMESTER HISTORY ---
    with tab4:
        st.subheader("Semester Summary")
        
        h_col1, h_col2, h_col3 = st.columns([1, 1, 2])
        with h_col1:
            class_id = st.number_input("Class ID", min_value=1, value=1)
        with h_col2:
            semester_id = st.number_input("Semester ID", min_value=1, value=1)
        with h_col3:
             st.write("") # spacer
             if st.button("Load Semester Data"):
                 try:
                    data = api_get(f"/teacher/semester-summary?class_id={class_id}&semester_id={semester_id}")
                    if data:
                        st.dataframe(data, use_container_width=True)
                    else:
                        st.info("No records found.")
                 except Exception as e:
                     st.error(f"Error: {e}")

