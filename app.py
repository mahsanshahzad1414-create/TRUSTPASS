"""
TRUSTPASS - Streamlit Application (Entry Point)
Main app that wires the UI, services, storage and session_state together.
"""
from datetime import timezone
import traceback
import streamlit as st

from src import ui, services, storage

# App meta
st.set_page_config(
    page_title="TRUSTPASS — AI Passport",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_TITLE = "TRUSTPASS"
APP_TAGLINE = "Your identity. Your context. Your permission."

# -- Initialize session state safely ------------------------------------------------
def init_session_state():
    defaults = {
        "current_user_id": None,
        "nav": "Overview",
        "demo_mode": True,
        "notifications_unread": 0,
        "refresh_key": 0,
        "pending_action": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Initialize services, storage
    if "store" not in st.session_state:
        st.session_state["store"] = storage.InMemoryStore()
    if "svc" not in st.session_state:
        st.session_state["svc"] = services.ServiceLayer(st.session_state["store"])
    # Ensure demo data available if demo_mode
    if st.session_state["demo_mode"] and not st.session_state["store"].has_demo_loaded():
        st.session_state["svc"].load_demo_data()
    # Ensure permission expiry refresh
    st.session_state["svc"].expire_permissions_check()


init_session_state()

svc: services.ServiceLayer = st.session_state["svc"]

# Top nav / header
try:
    ui.inject_css()
    ui.app_header(APP_TITLE, APP_TAGLINE, svc)
    # Sidebar navigation
    with st.sidebar:
        ui.sidebar_navigation(st.session_state)
    # Route pages
    page = st.session_state.get("nav", "Overview")
    if page == "Overview":
        ui.page_overview(svc)
    elif page == "My Passport":
        ui.page_my_passport(svc)
    elif page == "Credentials":
        ui.page_credentials(svc)
    elif page == "AI Access Requests":
        ui.page_access_requests(svc)
    elif page == "Permissions":
        ui.page_permissions(svc)
    elif page == "AI Agents":
        ui.page_agents(svc)
    elif page == "Access History":
        ui.page_access_history(svc)
    elif page == "Privacy Center":
        ui.page_privacy_center(svc)
    elif page == "Security Center":
        ui.page_security_center(svc)
    elif page == "Settings":
        ui.page_settings(svc)
    elif page == "Help / About":
        ui.page_help_about(svc)
    else:
        st.info("Page not found. Use the sidebar to navigate.")
except Exception as e:
    # Prevent exposing tracebacks to end users; log internally
    err_id = str(traceback.format_exc())[:8]
    st.error(f"An unexpected error occurred (ref {err_id}). Please try again.")
    # record to audit
    try:
        svc.audit.log_event(
            actor="system",
            action="application_error",
            resource="app.py",
            detail=f"Error: {str(e)}",
            owner=None,
        )
    except Exception:
        pass
    # show debug info if store.debug
    if st.session_state.get("store") and st.session_state["store"].debug:
        st.error("Debug details:")
        st.text(traceback.format_exc())
