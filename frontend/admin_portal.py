# frontend/admin_portal.py
import streamlit as st
import json
import urllib.request
import urllib.error
from datetime import date
from urllib.parse import quote

BACKEND_URL = "http://127.0.0.1:5000"

# ------------------ API HELPERS ------------------
def api_get(path):
    with urllib.request.urlopen(f"{BACKEND_URL}{path}") as r:
        return json.loads(r.read().decode("utf-8"))

def api_post(path, payload):
    req = urllib.request.Request(
        f"{BACKEND_URL}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode("utf-8"))

# =========================================================
# MAIN ADMIN PORTAL FUNCTION
# =========================================================
def run_admin_portal(on_exit):
    # ------------------ SESSION ------------------
    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    # ------------------ LOGIN SCREEN ------------------
    if not st.session_state.admin_logged_in:
        st.markdown("<br><br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div style="background-color: white; padding: 2rem; border-radius: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #e2e8f0;">
                <h2 style="text-align: center; color: #0f172a; border-bottom: none; margin-bottom: 1rem;">Administrator Login</h2>
                <p style="text-align: center; color: #64748b; margin-bottom: 0;">Authorized personnel only</p>
            </div>
            <br>
            """, unsafe_allow_html=True)

            admin_id = st.text_input("Admin ID")
            password = st.text_input("Password", type="password")

            if st.button("Access Portal", use_container_width=True):
                if not admin_id.strip() or not password.strip():
                    st.error("Credentials required.")
                    st.stop()

                try:
                    resp = api_post("/admin/login", {"admin_id": admin_id, "password": password})
                    st.session_state.admin_logged_in = True
                    st.session_state.admin_id = resp.get("admin_id")
                    st.session_state.admin_name = resp.get("name")
                    st.rerun()
                except Exception as e:
                    st.error(f"Login failed: {e}")

            st.markdown("---")
            if st.button("Back to Home"):
                on_exit()
        return

    # ------------------ SIDEBAR ------------------
    with st.sidebar:
        # Use a professional placeholder/logo or nothing, removing generic icon or using a local asset if available.
        st.title("Admin Panel")
        st.write(f"Logged in as: **{st.session_state.admin_name}**")
        
        menu = st.radio(
            "Navigation", 
            [
                "Student Registration",
                "Students Management",
                "Teachers Management",
                "Classes Calendar",
                "Periods & Schedule",
                "Substitutions",
                "System Analytics",
                "Audit Logs"
            ]
        )
        
        st.markdown("---")
        if st.button("Sign Out", use_container_width=True):
            st.session_state.admin_logged_in = False
            on_exit()
            st.rerun()

    # ------------------ PAGE ROUTING ------------------
    
    # 1. STUDENT REGISTRATION
    if menu == "Student Registration":
        st.header("Student Live Registration")
        st.markdown("Use this module to register new students with face data.")
        st.divider()
        
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                sid = st.text_input("Student ID")
                sname = st.text_input("Student Name")
            with col2:
                sdept = st.text_input("Department")
                sbatch = st.text_input("Batch")
            
            st.info("Clicking Register will open the camera on the server.")
            
            if st.button("Register Student"):
                if not sid or not sname:
                    st.error("ID and Name are mandatory.")
                else:
                    try:
                        resp = api_post("/admin/student/register-live", {
                            "student_id": sid, "name": sname, "department": sdept, "batch": sbatch
                        })
                        st.success("Student Registered Successfully!")
                        st.json(resp)
                    except Exception as e:
                        st.error(f"Error: {e}")

    # 2. STUDENTS LIST
    elif menu == "Students Management":
        st.header("Student Database")
        
        tab1, tab2 = st.tabs(["View Students", "Delete Actions"])
        
        with tab1:
            try:
                departments = ["All"] + api_get("/admin/departments")
                batches = ["All"] + api_get("/admin/batches")
                
                f1, f2 = st.columns(2)
                with f1: s_dept = st.selectbox("Filter Dept", departments)
                with f2: s_batch = st.selectbox("Filter Batch", batches)
                
                url = "/admin/students"
                params = []
                if s_dept != "All": params.append(f"department={quote(s_dept)}")
                if s_batch != "All": params.append(f"batch={quote(s_batch)}")
                if params: url += "?" + "&".join(params)
                
                data = api_get(url)
                st.write(f"**Total Students:** {len(data)}")
                st.dataframe(data, use_container_width=True)
            except Exception as e:
                st.error(f"Error loading students: {e}")

        with tab2:
            st.subheader("Delete Single Student")
            c1, c2 = st.columns(2)
            with c1:
                del_sid = st.text_input("Student ID to Delete")
            with c2:
                st.write("")
                st.write("")
                if st.button("Delete Student", type="primary"):
                    try:
                        api_post("/admin/students/delete", {"student_id": del_sid})
                        st.success(f"Deleted {del_sid}")
                    except Exception as e:
                        st.error(str(e))
                        
            st.divider()
            
            st.subheader("Bulk Delete Batch")
            b_del = st.selectbox("Select Batch", ["All"] + api_get("/admin/batches"))
            if st.button("DELETE ENTIRE BATCH"):
                if b_del == "All":
                    st.error("Select a specific batch.")
                else:
                    try:
                        api_post("/admin/students/bulk-delete", {"batch": b_del})
                        st.success(f"Batch {b_del} deleted.")
                    except Exception as e:
                        st.error(str(e))

    # 3. TEACHERS
    elif menu == "Teachers Management":
        st.header("Teachers Management")
        
        tab_a, tab_b = st.tabs(["List & Add", "Update & Delete"])
        
        with tab_a:
            st.subheader("Add New Teacher")
            with st.form("add_teacher"):
                c1, c2 = st.columns(2)
                t_id = c1.text_input("ID")
                t_name = c2.text_input("Name")
                t_email = c1.text_input("Email")
                t_dept = c2.text_input("Dept")
                t_pass = st.text_input("Password", type="password")
                
                if st.form_submit_button("Add Teacher"):
                    try:
                        api_post("/admin/teachers", {
                            "teacher_id": t_id, "name": t_name, "email": t_email,
                            "department": t_dept, "password": t_pass
                        })
                        st.success("Teacher Added!")
                    except Exception as e:
                        st.error(str(e))
            
            st.subheader("All Teachers")
            try:
                st.dataframe(api_get("/admin/teachers"), use_container_width=True)
            except:
                st.error("Failed to load list.")

        with tab_b:
            st.info("Use IDs to update or delete records.")
            upd_id = st.text_input("Teacher ID to Manage")
            if st.button("Delete Teacher"):
                try:
                    api_post("/admin/teachers/delete", {"teacher_id": upd_id})
                    st.success("Deleted.")
                except Exception as e:
                     st.error(str(e))

    # 4. CALENDAR
    elif menu == "Classes Calendar":
        st.header("Class Calendar")
        c1, c2, c3 = st.columns(3)
        cid = c1.number_input("Class ID", 1, value=1)
        cdate = c2.date_input("Date")
        is_work = c3.selectbox("Type", [True, False], format_func=lambda x: "Working" if x else "Holiday")
        
        reason = st.text_input("Reason / Note")
        if st.button("Update Calendar"):
            try:
                api_post("/admin/class-calendar", {
                    "class_id": cid, "date": str(cdate),
                    "is_working": is_work, "reason": reason
                })
                st.success("Calendar updated.")
            except Exception as e:
                st.error(str(e))
        
        st.subheader(f"Entries for Class {cid}")
        try:
            st.dataframe(api_get(f"/admin/class-calendar/{cid}"), use_container_width=True)
        except:
             pass

    # 5. PERIODS
    elif menu == "Periods & Schedule":
        st.header("Periods Configuration")
        with st.expander("Add New Period", expanded=True):
            with st.form("period_form"):
                c1, c2, c3 = st.columns(3)
                p_tid = c1.text_input("Teacher ID")
                p_start = c2.text_input("Start (HH:MM:SS)", "09:00:00")
                p_end = c3.text_input("End (HH:MM:SS)", "09:45:00")
                p_cls = c1.number_input("Class ID", 1)
                p_sem = c2.number_input("Semester ID", 1)
                p_sub = c3.number_input("Subject ID", 1)
                
                if st.form_submit_button("Create Period"):
                    try:
                        api_post("/admin/periods", {
                            "teacher_id": p_tid, "start_time": p_start, "end_time": p_end,
                            "grace_minutes": 5, "class_id": p_cls,
                            "semester_id": p_sem, "subject_id": p_sub
                        })
                        st.success("Period created.")
                    except Exception as e:
                        st.error(str(e))
        
        st.markdown("### Existing Periods")
        try:
            st.dataframe(api_get("/admin/periods"), use_container_width=True)
        except:
            pass

    # 6. SUBSTITUTIONS
    elif menu == "Substitutions":
        st.header("Substitutions")
        with st.form("sub_form"):
            c1, c2 = st.columns(2)
            s_orig = c1.text_input("Original Teacher ID")
            s_sub = c2.text_input("Substitute Teacher ID")
            s_pid = c1.number_input("Period ID", 1)
            s_date = c2.date_input("Date")
            
            if st.form_submit_button("Assign Substitution"):
                try:
                    api_post("/admin/substitutions", {
                        "date": str(s_date), "period_id": s_pid,
                        "original_teacher_id": s_orig, "substitute_teacher_id": s_sub
                    })
                    st.success("Substitution assigned.")
                except Exception as e:
                    st.error(str(e))
        
        st.subheader("Active Substitutions")
        st.dataframe(api_get("/admin/substitutions"), use_container_width=True)

    # 7. ANALYTICS
    elif menu == "System Analytics":
        st.header("System Analytics")
        c1, c2 = st.columns(2)
        cid = c1.number_input("Class ID", 1)
        semid = c2.number_input("Semester ID", 1)
        
        if st.button("Generate Report"):
            try:
                data = api_get(f"/admin/analytics/class-semester?class_id={cid}&semester_id={semid}")
                st.dataframe(data, use_container_width=True)
            except Exception as e:
                st.error(str(e))

    # 8. LOGS
    elif menu == "Audit Logs":
        st.header("Audit Logs")
        try:
            st.dataframe(api_get("/admin/audit-logs"), use_container_width=True)
        except:
             st.info("No logs available.")
