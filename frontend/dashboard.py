import streamlit as st
import json
import urllib.request
import urllib.error
from datetime import date, datetime

# 1. SETUP PAGE CONFIG WITH WIDE LAYOUT (To match dashboard width)
st.set_page_config(page_title="Attendance Management System – Teacher Portal", layout="wide", initial_sidebar_state="expanded")

BACKEND_URL = "http://127.0.0.1:5000"

# ---------------- CUSTOM CSS FOR DARK DASHBOARD THEME ----------------
st.markdown("""
<style>
    /* Main Background - Deep Black */
    .stApp {
        background-color: #000000;
        color: #ffffff;
    }
    
    /* Sidebar Background - Slightly lighter black */
    [data-testid="stSidebar"] {
        background-color: #050505;
        border-right: 1px solid #333;
    }

    /* Metric/Card Styling */
    div[data-testid="metric-container"] {
        background-color: #111111;
        border: 1px solid #222;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    div[data-testid="metric-container"] label {
        color: #888; /* Grey text for labels */
    }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        color: #ffffff; /* White text for values */
    }

    /* Primary Blue Buttons (Matches the blue in your image) */
    div.stButton > button {
        background-color: #2962ff; 
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
        width: 100%;
    }
    div.stButton > button:hover {
        background-color: #0039cb;
        color: white;
    }

    /* Inputs (Text, Date, Select) - Dark Theme */
    .stTextInput>div>div>input, .stDateInput>div>div>input, .stSelectbox>div>div>div {
        background-color: #111111;
        color: white;
        border: 1px solid #333;
        border-radius: 5px;
    }
    
    /* Tables/Dataframes */
    [data-testid="stDataFrame"], [data-testid="stTable"] {
        background-color: #111111;
        border-radius: 10px;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #ffffff;
        font-family: 'Segoe UI', sans-serif;
    }
    
    /* Custom separator line */
    hr {
        border-color: #333;
    }
</style>
""", unsafe_allow_html=True)

# ---------------- STATE MANAGEMENT ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "teacher_id" not in st.session_state:
    st.session_state.teacher_id = None

# ---------------- API FUNCTIONS ----------------
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
        return json.loads(r.read().decode("utf-8"))

# ---------------- LOGIN SCREEN ----------------
if not st.session_state.logged_in:
    # Centering the login box visually
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("Teacher Portal")
        st.markdown("Please sign in to access the AI Attendance System")

        with st.container(border=True):
            teacher_id = st.text_input("Teacher ID", placeholder="Ex: T-101")
            password = st.text_input("Password", type="password")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Login"):
                if teacher_id.strip() == "" or password.strip() == "":
                    st.error("Please enter Teacher ID and Password.")
                    st.stop()

                try:
                    resp = api_post("/teacher/login", {"teacher_id": teacher_id.strip(), "password": password})
                    st.session_state.logged_in = True
                    st.session_state.teacher_id = resp.get("teacher_id")
                    st.rerun()
                except urllib.error.HTTPError as e:
                    st.error(f"Login failed (HTTP {e.code})")
                except Exception as e:
                    st.error("Backend not reachable.")
                    st.code(str(e))
    st.stop()

# ---------------- DASHBOARD LOGIC ----------------
context = None
try:
    context = api_get(f"/attendance/current-period/{st.session_state.teacher_id}")
except Exception as e:
    context = {"active": False, "message": "Backend not reachable", "error": str(e)}

# Sidebar Navigation (Simulating the left bar in the image)
with st.sidebar:
    st.title("Teacher Menu")
    st.markdown(f"Logged in as: **{st.session_state.teacher_id}**")
    st.divider()
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.teacher_id = None
        st.rerun()

st.title("Dashboard")

if not context.get("active"):
    st.warning(context.get("message", "No active period right now."))
    if context.get("error"):
        st.code(context["error"])
    st.stop()

# edit window check (real compare)
now_t = datetime.now().time()
deadline_t = datetime.strptime(context["edit_deadline"], "%H:%M").time()
edit_allowed = now_t <= deadline_t

# ---------------- TOP METRICS ROW (CARD STYLE) ----------------
# Using columns to create the card layout seen in the image
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric(label="Teacher Name", value=context.get("teacher_name", "Teacher"))
with m2:
    st.metric(label="Teacher ID", value=context.get("teacher_id"))
with m3:
    st.metric(label="Current Period", value=f"{context['period_start']} – {context['period_end']}")
with m4:
    st.metric(label="Edit Deadline", value=context["edit_deadline"], delta="Active" if edit_allowed else "Closed", delta_color="normal")

st.markdown("---")

# ---------------- MAIN CONTENT GRID ----------------
# Create a 2-column layout for the analytics tables to mimic charts
row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.subheader("Attendance Summary")
    if st.button("Load Summary Data", key="btn_summary"):
        try:
            data = api_get("/attendance/analytics")
            # Using dataframe with width scaling to look like a widget
            st.dataframe(data, use_container_width=True, hide_index=True) 
        except Exception as e:
            st.error("Failed to load analytics")

with row2_col2:
    st.subheader("Defaulters List")
    if st.button("Load Defaulters", key="btn_defaulters"):
        try:
            data = api_get("/attendance/defaulters")
            st.dataframe(data, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error("Failed to load defaulters")

st.markdown("<br>", unsafe_allow_html=True)

# ---------------- ACTION PANEL (MANUAL CORRECTION) ----------------
# Wrapped in a container to distinguish it as an 'Action' area
with st.container(border=True):
    st.subheader("Manual Attendance Correction")
    st.caption(f"Correction window closes at {context['edit_deadline']}.")
    
    c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
    
    with c1:
        student_id = st.text_input("Student ID", placeholder="Enter ID")
    with c2:
        attendance_date = st.date_input("Date", value=date.today())
    with c3:
        new_status = st.selectbox("Status", ["Present", "Late", "Absent"])
    with c4:
        st.markdown("<br>", unsafe_allow_html=True) # Spacer to align button
        submit = st.button("Update", disabled=not edit_allowed, type="primary")

    if submit:
        if student_id.strip() == "":
            st.error("Please enter Student ID.")
        else:
            payload = {
                "teacher_id": st.session_state.teacher_id,
                "student_id": student_id.strip(),
                "date": str(attendance_date),
                "status": new_status
            }
            try:
                api_post("/attendance/edit", payload)
                st.success(f"Attendance for {student_id} updated to {new_status}")
            except urllib.error.HTTPError as e:
                st.error("Update failed")
            except Exception as e:
                st.error("Backend error")

# ---------------- BOTTOM PANEL ----------------
st.markdown("---")
st.subheader("Semester Reports")

with st.container():
    sc1, sc2, sc3 = st.columns([1, 1, 2])
    with sc1:
        class_id = st.number_input("Class ID", min_value=1, value=1)
    with sc2:
        semester_id = st.number_input("Semester ID", min_value=1, value=1)
    with sc3:
        st.markdown("<br>", unsafe_allow_html=True)
        load_sem = st.button("Load Report")

    if load_sem:
        try:
            data = api_get(f"/teacher/semester-summary?class_id={class_id}&semester_id={semester_id}")
            st.dataframe(data, use_container_width=True)
        except urllib.error.HTTPError as e:
            st.error(f"Failed (HTTP {e.code})")
        except Exception as e:
            st.error("Backend not reachable")