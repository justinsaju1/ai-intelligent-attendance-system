import streamlit as st
import base64

from admin_portal import run_admin_portal
from dashboard import run_teacher_portal

# Configure page settings
st.set_page_config(
    page_title="Attendance Management System",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

import os

# Function to load CSS
def load_css(file_name):
    # Get absolute path to ensure it works from any CWD
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "assets", "style.css")
    
    try:
        with open(file_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"CSS file not found at: {file_path}")

# Load the custom CSS
load_css("style.css")

# Which screen is active?
if "screen" not in st.session_state:
    st.session_state.screen = "home"

def go_home():
    st.session_state.screen = "home"
    st.rerun()

# ---------------- HOME PAGE ----------------
if st.session_state.screen == "home":
    
    # Hero Section
    st.markdown("""
    <div style="text-align: center; padding: 4rem 1rem 3rem 1rem;">
        <h1 style="color: #0f172a; margin-bottom: 0.5rem;">Intelligent Attendance System</h1>
        <p class="subtext" style="font-size: 1.1rem;">Secure • Automated • Real-time</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Spacer
    st.write("")
    
    # Centered Layout for Cards
    col_spacer_l, col_teacher, col_spacer_m, col_admin, col_spacer_r = st.columns([1, 6, 1, 6, 1])
    
    with col_teacher:
        st.markdown("""
        <div class="custom-card">
            <h3>Teacher Portal</h3>
            <p>Manage daily attendance records, view class analytics, and submit manual corrections.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Access Teacher Portal", use_container_width=True):
            st.session_state.screen = "teacher"
            st.rerun()
            
    with col_admin:
        st.markdown("""
        <div class="custom-card">
            <h3>Administrator Portal</h3>
            <p>System configuration, user management, comprehensive reporting, and audit logs.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Access Admin Portal", use_container_width=True):
            st.session_state.screen = "admin"
            st.rerun()

    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: #64748b; font-size: 0.8rem; padding: 20px;'>© 2026 Attendance Management System</div>", unsafe_allow_html=True)

# ---------------- TEACHER ----------------
elif st.session_state.screen == "teacher":
    run_teacher_portal(go_home)

# ---------------- ADMIN ----------------
elif st.session_state.screen == "admin":
    run_admin_portal(go_home)

