"""
TRUSTPASS — Streamlit entrypoint

Run:
    streamlit run app.py

This file wires UI, services, storage and session state together.
"""
from datetime import timezone
import traceback

import streamlit as st

from src import ui
from src.storage import InMemoryStore
from src.services import ServiceLayer

# Page config
st.set_page_config(
    page_title="TRUSTPASS — Your Identity. Your Context. Your Permission.",
    page_icon="assets/brand/favicon.svg",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_session():
    # minimal defaults
    defaults = {
        "nav": "Overview",
        "demo_mode": True,
        "refresh": 0,
        "require_sensitive_confirmation": True,
        "auto_expire_permissions": True,
        "default_permission_hours": 168,
        "notification_prefs": {"new_request": True, "permission_expiry": True, "security": True},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    if "store" not in st.session_state:
        st.session_state["store"] = InMemoryStore()
    if "svc" not in st.session_state:
        st.session_state["svc"] = ServiceLayer(st.session_state["store"])


init_session()
svc = st.session_state["svc"]

# UI
try:
    ui.inject_css()
    ui.app_header("TRUSTPASS", "Your Identity. Your Context. Your Permission.", svc)
    with st.sidebar:
        ui.sidebar_navigation(st.session_state)
    page = st.session_state.get("nav", "Overview")
    # route
    if page == "Overview":
        ui.page_overview(svc)
    elif page == "My AI Passport":
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
    elif page == "Notifications":
        ui.page_notifications(svc)
    elif page == "Settings":
        ui.page_settings(svc)
    elif page == "Help / About":
        ui.page_help_about(svc)
    else:
        st.info("Page not found. Use the sidebar to navigate.")
except Exception as e:
    # Do not display raw tracebacks to end users
    err_id = "ERR-APP"
    st.error(f"An unexpected error occurred ({err_id}). Please refresh or contact support.")
    try:
        svc.audit.log_event(actor="system", action="application_error", resource="app", detail=str(e), owner_id=None)
    except Exception:
        pass
    # If in debug mode, optionally show details
    if getattr(st.session_state.get("store"), "debug", False):
        st.text(traceback.format_exc())
