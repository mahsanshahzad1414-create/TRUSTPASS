"""
UI components and pages for TRUSTPASS.
Provides premium dark theme, navigation, and functional pages wired to ServiceLayer.
"""
from typing import List, Optional, Dict
from datetime import datetime, timezone
import streamlit as st
import pandas as pd
from .models import DEFAULT_USER_ID
from . import security


CSS = f"""
:root{{
  --bg: #0B1220;
  --card: rgba(18,24,36,0.85);
  --muted: #94a3b8;
  --accent: #7C3AED; /* violet */
  --accent-2: #06B6D4; /* cyan */
  --success: #10B981;
  --warn: #F59E0B;
  --danger: #EF4444;
}}
/* basic layout */
body {{ background-color: var(--bg); color: #e6eef6; }}
.stApp {{ background-color: transparent; }}
header[role="banner"] {{ display:none; }}
.sidebar .block-container {{ background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01)); padding: 16px; }}
.card {{ background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01)); padding: 16px; border-radius:10px; box-shadow: 0 6px 18px rgba(2,6,23,0.6); border:1px solid rgba(255,255,255,0.03); }}
.kpi {{ font-size:20px; font-weight:700; color: #fff; }}
.small {{ font-size:13px; color:var(--muted); }}
.badge {{ background: rgba(255,255,255,0.03); padding:6px 10px; border-radius:999px; color:var(--muted); font-size:12px; display:inline-block; }}
.logo-word {{ font-weight:700; letter-spacing:1px; font-size:18px; color:#fff; }}
.logo-tag {{ font-size:11px; color:var(--muted); }}
.btn-primary {{ background: linear-gradient(90deg,var(--accent),var(--accent-2)); color: white; padding:8px 12px; border-radius:8px; }}
.field-sens-low {{ color: var(--accent-2); }}
.field-sens-medium {{ color: var(--warn); }}
.field-sens-high {{ color: var(--danger); font-weight:700; }}

@media(max-width: 600px) {
  .kpi { font-size:16px; }
}
"""


def inject_css():
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


def _logo_html(variant: str = "full") -> str:
    # variant: full|mark|light
    if variant == "mark":
        path = "assets/brand/trustpass-mark.svg"
    else:
        path = "assets/brand/trustpass-logo.svg"
    return f"<img src='{path}' style='height:36px' alt='TRUSTPASS logo'/>"


def app_header(title: str, tagline: str, svc):
    cols = st.columns([1, 4, 2])
    with cols[0]:
        st.markdown(_logo_html("mark"), unsafe_allow_html=True)
    with cols[1]:
        st.markdown(f"<div style='padding-left:8px'><div class='logo-word'>{title}</div><div class='logo-tag'>{tagline}</div></div>", unsafe_allow_html=True)
    with cols[2]:
        # demo toggle
        demo = st.session_state.get("demo_mode", True)
        new_demo = st.checkbox("Demo Mode", value=demo, key="ui_demo_toggle")
        st.session_state["demo_mode"] = new_demo
        # notifications
        notes = svc.notify.list_notifications(DEFAULT_USER_ID)
        unread = sum(1 for n in notes if n.unread)
        st.markdown(f"<div style='text-align:right'><span class='badge'>Notifications: {unread}</span></div>", unsafe_allow_html=True)


def sidebar_navigation(ss):
    st.markdown(_logo_html("full"), unsafe_allow_html=True)
    st.markdown("<div style='margin-top:8px'><div class='logo-word'>TRUSTPASS</div><div class='small'>Your Identity. Your Context. Your Permission.</div></div>", unsafe_allow_html=True)
    st.markdown("---")
    pages = [
        "Overview",
        "My AI Passport",
        "Credentials",
        "AI Access Requests",
        "Permissions",
        "AI Agents",
        "Access History",
        "Privacy Center",
        "Security Center",
        "Notifications",
        "Settings",
        "Help / About",
    ]
    choice = st.radio("", options=pages, index=pages.index(ss.get("nav","Overview")), key="nav_radio")
    ss["nav"] = choice
    st.markdown("---")
    if st.button("Reset Demo Data"):
        ss["svc"].load_demo_data()
        st.success("Demo data reset")


# ------------------------------
# Utility helpers
# ------------------------------

def human_timedelta(dt: Optional[datetime]):
    if not dt:
        return "No expiry"
    now = datetime.now(timezone.utc)
    delta = dt - now
    total_sec = int(delta.total_seconds())
    if total_sec <= 0:
        return "Expired"
    days = total_sec // 86400
    hours = (total_sec % 86400) // 3600
    return f"{days}d {hours}h"


# ------------------------------
# Pages
# ------------------------------

def page_overview(svc):
    st.markdown("<div class='card'><h3>Overview</h3></div>", unsafe_allow_html=True)
    owner = DEFAULT_USER_ID
    user = svc.storage.get_user(owner)
    if not user:
        st.info("No user profile. Load demo data in the sidebar.")
        return
    health = svc.compute_passport_health(owner)
    privacy = svc.compute_privacy_score(owner)
    perms = svc.list_permissions(owner)
    creds = svc.storage.list_credentials(owner)
    agents = svc.list_agents()
    verified_creds = len([c for c in creds if c.status=="Verified"]) 
    active_perms = [p for p in perms if p.status=="ACTIVE"]
    pending_reqs = svc.list_requests(owner)
    sensitive_shared = sum(1 for p in active_perms for f in p.fields if svc.classify_field(f)=="high")

    cols = st.columns(4)
    cols[0].markdown(f"<div class='card'><div class='small'>Passport Health</div><div class='kpi'>{health['score']}%</div></div>", unsafe_allow_html=True)
    cols[1].markdown(f"<div class='card'><div class='small'>Privacy Score</div><div class='kpi'>{privacy['score']}%</div></div>", unsafe_allow_html=True)
    cols[2].markdown(f"<div class='card'><div class='small'>Verified Credentials</div><div class='kpi'>{verified_creds}</div></div>", unsafe_allow_html=True)
    cols[3].markdown(f"<div class='card'><div class='small'>Active AI Agents</div><div class='kpi'>{len(set([p.agent_id for p in perms if p.status=='ACTIVE']))}</div></div>", unsafe_allow_html=True)

    cols2 = st.columns(4)
    cols2[0].markdown(f"<div class='card'><div class='small'>Active Permissions</div><div class='kpi'>{len(active_perms)}</div></div>", unsafe_allow_html=True)
    cols2[1].markdown(f"<div class='card'><div class='small'>Pending Requests</div><div class='kpi'>{len(pending_reqs)}</div></div>", unsafe_allow_html=True)
    cols2[2].markdown(f"<div class='card'><div class='small'>Sensitive Data Shared</div><div class='kpi'>{sensitive_shared}</div></div>", unsafe_allow_html=True)
    cols2[3].markdown(f"<div class='card'><div class='small'>Trust Score (avg)</div><div class='kpi'>{int(sum(a.trust_score for a in agents)/len(agents)) if agents else 0}</div></div>", unsafe_allow_html=True)

    st.markdown("<h4>Recent activity</h4>", unsafe_allow_html=True)
    events = sorted(svc.storage.list_audit(owner), key=lambda e: e.timestamp, reverse=True)[:8]
    if not events:
        st.info("No recent activity")
    else:
        for e in events:
            ts = e.timestamp.strftime('%Y-%m-%d %H:%M UTC')
            st.markdown(f"- **{e.action.replace('_',' ').title()}** — {e.detail} <span class='small'>{ts}</span>", unsafe_allow_html=True)

    st.markdown("<h4>Security recommendations</h4>", unsafe_allow_html=True)
    recs = []
    if any(p.status=="ACTIVE" and p.expires_at and (p.expires_at - datetime.now(timezone.utc)).days < 3 for p in perms):
        recs.append("⚠ Review expiring permissions")
    if any(len(p.fields) >= 4 and p.status=="ACTIVE" for p in perms):
        recs.append("⚠ Reduce broad access for some agents")
    if not recs:
        st.success("No immediate recommendations")
    else:
        for r in recs:
            st.warning(r)


def page_my_passport(svc):
    st.markdown("<div class='card'><h3>My AI Passport</h3></div>", unsafe_allow_html=True)
    owner = DEFAULT_USER_ID
    user = svc.storage.get_user(owner)
    if not user:
        st.info("No profile found. Load demo data.")
        return
    cols = st.columns([3,1])
    with cols[0]:
        st.markdown(f"### {user.display_name}")
        st.markdown(f"- Country: {user.country}")
        st.markdown(f"- Language: {user.language}")
        st.markdown(f"- Verification: {'VERIFIED' if user.verified else 'UNVERIFIED'}")
        st.markdown(f"- Last verified: {user.last_verified_at}")
        if st.button("Export Passport JSON"):
            data = svc.export_passport_json(owner)
            st.download_button(label="Download passport.json", data=data, file_name="passport.json", mime="application/json")
    with cols[1]:
        st.markdown("<div class='card'><div class='small'>Passport</div><div style='font-size:18px'>••••••••4821</div></div>", unsafe_allow_html=True)
        if st.button("Unmask Passport (confirm)"):
            with st.form("unmask_form"):
                st.write("Unmasking will reveal sensitive information. Confirm to proceed.")
                confirm = st.checkbox("I understand the sensitivity and want to unmask the passport")
                submit = st.form_submit_button("Confirm")
                if submit and confirm:
                    st.info("Sensitive data revealed in a real product after secure confirmation")

    st.markdown("#### Credentials")
    creds = svc.storage.list_credentials(owner)
    if not creds:
        st.info("No credentials added yet.")
    else:
        for c in creds:
            with st.expander(f"{c.name} — {c.type} — {c.status}"):
                st.write(f"Issuer: {c.issuer}")
                st.write(f"Sensitivity: {c.sensitivity}")
                st.write(f"Sharing allowed: {'Yes' if c.sharing_allowed else 'No'}")


def page_credentials(svc):
    st.markdown("<div class='card'><h3>Credential Vault</h3></div>", unsafe_allow_html=True)
    owner = DEFAULT_USER_ID
    creds = svc.storage.list_credentials(owner)
    df = pd.DataFrame([{
        "Name": c.name,
        "Type": c.type,
        "Issuer": c.issuer,
        "Status": c.status,
        "Sensitivity": c.sensitivity,
        "Sharing": 'Allowed' if c.sharing_allowed else 'Blocked',
        "ID": c.credential_id
    } for c in creds])
    st.dataframe(df)

    st.markdown("### Add Credential")
    with st.form("add_cred"):
        name = st.text_input("Name")
        issuer = st.text_input("Issuer", value="Self")
        ctype = st.selectbox("Type", ["Education","Academic Record","Degree","Skills","Language","Certifications","Work Experience","Identity","Other"]) 
        sensitivity = st.selectbox("Sensitivity", ["low","medium","high"])
        status = st.selectbox("Status", ["Verified","Pending","Expired","Revoked"]) 
        issue = st.date_input("Issue date (optional)")
        expiry = st.date_input("Expiry date (optional)")
        sharing = st.checkbox("Allow sharing by default", value=True)
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Add Credential")
        if submitted:
            try:
                data = {
                    "name": name,
                    "issuer": issuer,
                    "type": ctype,
                    "sensitivity": sensitivity,
                    "status": status,
                    "issue_date": None,
                    "expiry_date": None,
                    "sharing_allowed": sharing,
                    "notes": notes,
                }
                if name.strip()=="":
                    st.error("Name is required")
                else:
                    svc.add_credential(owner, data)
                    st.success("Credential added")
            except Exception as e:
                st.error(str(e))

    st.markdown("### Manage Credentials")
    if not creds:
        st.info("No credentials yet")
    else:
        for c in creds:
            with st.expander(f"{c.name} ({c.type})"):
                st.write(f"Issuer: {c.issuer}")
                st.write(f"Status: {c.status}")
                cols = st.columns(4)
                if cols[0].button("Verify", key=f"verify_{c.credential_id}"):
                    try:
                        svc.verify_credential(c.credential_id, DEFAULT_USER_ID)
                        st.success("Credential verified")
                    except Exception as e:
                        st.error(str(e))
                if cols[1].button("Edit", key=f"edit_{c.credential_id}"):
                    with st.form(f"edit_form_{c.credential_id}"):
                        name = st.text_input("Name", value=c.name)
                        issuer = st.text_input("Issuer", value=c.issuer)
                        status = st.selectbox("Status", ["Verified","Pending","Expired","Revoked"], index=["Verified","Pending","Expired","Revoked"].index(c.status))
                        sharing = st.checkbox("Allow sharing", value=c.sharing_allowed)
                        save = st.form_submit_button("Save")
                        if save:
                            svc.edit_credential(c.credential_id, {"name":name, "issuer":issuer, "status":status, "sharing_allowed":sharing})
                            st.success("Credential updated")
                if cols[2].button("Delete", key=f"del_{c.credential_id}"):
                    with st.form(f"del_confirm_{c.credential_id}"):
                        st.write("Type the credential name to confirm deletion")
                        typed = st.text_input("Confirm name")
                        confirm = st.form_submit_button("Delete")
                        if confirm:
                            if typed == c.name:
                                svc.remove_credential(c.credential_id, DEFAULT_USER_ID)
                                st.success("Credential deleted")
                            else:
                                st.error("Name mismatch. Deletion cancelled.")
                if cols[3].button("Toggle Sharing", key=f"sharebtn_{c.credential_id}"):
                    # open form to change sharing only
                    with st.form(f"share_form_{c.credential_id}"):
                        allow = st.checkbox("Allow sharing", value=c.sharing_allowed)
                        ok = st.form_submit_button("Save")
                        if ok:
                            svc.edit_credential(c.credential_id, {"sharing_allowed": allow})
                            st.success("Sharing preference updated")


def page_access_requests(svc):
    st.markdown("<div class='card'><h3>AI Access Requests</h3></div>", unsafe_allow_html=True)
    owner = DEFAULT_USER_ID
    reqs = svc.list_requests(owner)
    if not reqs:
        st.info("No pending requests")
        return
    for r in reqs:
        agent = svc.storage.get_agent(r.agent_id)
        with st.expander(f"{agent.name if agent else r.agent_id} — {r.purpose}", expanded=True):
            st.write(f"Organization: {agent.organization if agent else 'Unknown'}")
            st.write(f"Reason: {r.reason}")
            st.write(f"Requested duration: {r.requested_duration_hours} hours")
            st.write("Requested fields:")
            rec = svc.recommend_minimum_fields(r.requested_fields)
            st.markdown(f"<div class='small'>Recommendation: {', '.join(rec)}</div>", unsafe_allow_html=True)
            selections = {}
            for f in r.requested_fields:
                default = True if f in rec else False
                selections[f] = st.checkbox(f"{f} ({svc.classify_field(f)})", value=default, key=f"{r.request_id}_{f}")
            cols = st.columns(3)
            if cols[0].button("Approve selected", key=f"approve_{r.request_id}"):
                approved = [f for f,v in selections.items() if v]
                if not approved:
                    st.error("Select at least one field to approve")
                else:
                    # confirm if any high sensitivity and setting enabled
                    highs = [f for f in approved if svc.classify_field(f)=="high"]
                    if highs and st.session_state.get("require_sensitive_confirmation", True):
                        with st.form(f"confirm_approve_{r.request_id}"):
                            st.write("High-sensitivity fields selected: "+", ".join(highs))
                            chk = st.checkbox("I confirm sharing these high-sensitivity fields")
                            ok = st.form_submit_button("Confirm and Approve")
                            if ok and chk:
                                svc.approve_request(r.request_id, approved, r.requested_duration_hours, DEFAULT_USER_ID)
                                st.success("Access granted")
                    else:
                        svc.approve_request(r.request_id, approved, r.requested_duration_hours, DEFAULT_USER_ID)
                        st.success("Access granted")
            if cols[1].button("Approve recommended", key=f"approve_min_{r.request_id}"):
                approved = rec
                highs = [f for f in approved if svc.classify_field(f)=="high"]
                if highs and st.session_state.get("require_sensitive_confirmation", True):
                    with st.form(f"confirm_min_{r.request_id}"):
                        st.write("High-sensitivity fields included: "+", ".join(highs))
                        chk = st.checkbox("I confirm")
                        ok = st.form_submit_button("Confirm and Approve")
                        if ok and chk:
                            svc.approve_request(r.request_id, approved, r.requested_duration_hours, DEFAULT_USER_ID)
                            st.success("Access granted")
                else:
                    svc.approve_request(r.request_id, approved, r.requested_duration_hours, DEFAULT_USER_ID)
                    st.success("Access granted")
            if cols[2].button("Deny", key=f"deny_{r.request_id}"):
                with st.form(f"deny_form_{r.request_id}"):
                    reason = st.text_area("Reason for denial (optional)")
                    ok = st.form_submit_button("Deny request")
                    if ok:
                        svc.deny_request(r.request_id, DEFAULT_USER_ID, reason)
                        st.success("Request denied")


def page_permissions(svc):
    st.markdown("<div class='card'><h3>Permissions Center</h3></div>", unsafe_allow_html=True)
    owner = DEFAULT_USER_ID
    perms = svc.list_permissions(owner)
    if not perms:
        st.info("No permissions recorded.")
        return
    for p in perms:
        agent = svc.storage.get_agent(p.agent_id)
        remaining = human_timedelta(p.expires_at)
        with st.expander(f"{agent.name if agent else p.agent_id} — {p.status}"):
            st.write(f"Purpose: {p.purpose}")
            st.write(f"Fields: {', '.join(p.fields)}")
            st.write(f"Granted at: {p.granted_at}")
            st.write(f"Expires at: {p.expires_at} — {remaining}")
            cols = st.columns(3)
            if cols[0].button("Revoke", key=f"revoke_{p.permission_id}"):
                with st.form(f"revoke_confirm_{p.permission_id}"):
                    st.write("Revoke will immediately remove access. Type REVOKE to confirm.")
                    typed = st.text_input("Type REVOKE to confirm")
                    confirm = st.form_submit_button("Revoke")
                    if confirm:
                        if typed == "REVOKE":
                            svc.revoke_permission(p.permission_id, DEFAULT_USER_ID, reason="User revoked")
                            st.success("Permission revoked")
                        else:
                            st.error("Confirmation failed. Type REVOKE exactly.")
            if cols[1].button("Extend", key=f"extend_{p.permission_id}"):
                with st.form(f"extend_form_{p.permission_id}"):
                    opt = st.selectbox("Extend by", ["1 hour","24 hours","7 days","30 days","Custom hours"]) 
                    custom = None
                    if opt == "Custom hours":
                        custom = st.number_input("Hours", min_value=1, max_value=24*365, value=24)
                    ok = st.form_submit_button("Extend")
                    if ok:
                        hours = 1 if opt=="1 hour" else 24 if opt=="24 hours" else 168 if opt=="7 days" else 720 if opt=="30 days" else custom
                        try:
                            svc.extend_permission(p.permission_id, int(hours), DEFAULT_USER_ID)
                            st.success("Permission extended")
                        except Exception as e:
                            st.error(str(e))
            if cols[2].button("Modify Fields", key=f"mod_{p.permission_id}"):
                with st.form(f"mod_form_{p.permission_id}"):
                    all_fields = p.fields.copy()
                    # For demo purposes allow user to remove fields
                    new_fields = st.multiselect("Fields to grant", options=p.fields, default=p.fields)
                    ok = st.form_submit_button("Save")
                    if ok:
                        svc.modify_permission_fields(p.permission_id, new_fields, DEFAULT_USER_ID)
                        st.success("Permission updated")


def page_agents(svc):
    st.markdown("<div class='card'><h3>AI Agent Directory</h3></div>", unsafe_allow_html=True)
    agents = svc.list_agents()
    if not agents:
        st.info("No agents registered.")
        return
    owner = DEFAULT_USER_ID
    perms = svc.list_permissions(owner)
    for a in agents:
        shared = []
        requested = a.requested_fields
        for p in perms:
            if p.agent_id == a.agent_id and p.status=="ACTIVE":
                shared.extend(p.fields)
        blocked = [f for f in requested if f not in shared]
        st.markdown(f"<div class='card'><b>{a.name}</b> — {a.organization} — Trust {a.trust_score}</div>", unsafe_allow_html=True)
        cols = st.columns([3,1])
        with cols[0]:
            st.write(a.description)
            st.write(f"Requested: {', '.join(requested)}")
            st.write(f"Shared: {', '.join(shared) if shared else 'None'}")
            st.write(f"Blocked: {', '.join(blocked) if blocked else 'None'}")
        with cols[1]:
            st.write(f"Verified: {'Yes' if a.verified else 'No'}")
            st.write(f"Last activity: {a.last_activity}")


def page_access_history(svc):
    st.markdown("<div class='card'><h3>Access History / Audit Log</h3></div>", unsafe_allow_html=True)
    owner = DEFAULT_USER_ID
    events = svc.storage.list_audit(owner)
    if not events:
        st.info("No audit events yet.")
        return
    df = pd.DataFrame([{"timestamp": e.timestamp, "actor": e.actor, "action": e.action, "resource": e.resource, "detail": e.detail} for e in events])
    st.dataframe(df.sort_values("timestamp", ascending=False))
    if st.button("Export Audit CSV"):
        csv_bytes = svc.export_audit_csv(owner)
        st.download_button(label="Download audit.csv", data=csv_bytes, file_name="audit.csv", mime="text/csv")


def page_privacy_center(svc):
    st.markdown("<div class='card'><h3>Privacy Center</h3></div>", unsafe_allow_html=True)
    owner = DEFAULT_USER_ID
    p = svc.compute_privacy_score(owner)
    st.markdown(f"<div class='card'><div class='small'>Privacy Score</div><div class='kpi'>{p['score']}%</div></div>", unsafe_allow_html=True)
    st.write("How this score was calculated:")
    st.json(p['details'])
    if p['score'] < 50:
        st.warning("Consider reducing shared high-sensitivity fields or revoke broad permissions.")
    else:
        st.success("Privacy posture looks reasonable for demo data.")


def page_security_center(svc):
    st.markdown("<div class='card'><h3>Security Center</h3></div>", unsafe_allow_html=True)
    st.write("Security settings")
    if "require_sensitive_confirmation" not in st.session_state:
        st.session_state["require_sensitive_confirmation"] = True
    if "auto_expire_permissions" not in st.session_state:
        st.session_state["auto_expire_permissions"] = True
    st.session_state["require_sensitive_confirmation"] = st.checkbox("Require confirmation for high-sensitivity fields", value=st.session_state["require_sensitive_confirmation"])
    st.session_state["auto_expire_permissions"] = st.checkbox("Automatically expire permissions when time passes", value=st.session_state["auto_expire_permissions"])
    st.write("Recent security events:")
    events = [e for e in svc.storage.list_audit(DEFAULT_USER_ID) if 'permission' in e.action or 'credential' in e.action]
    for e in sorted(events, key=lambda x: x.timestamp, reverse=True)[:10]:
        st.write(f"{e.timestamp} — {e.action} — {e.detail}")


def page_notifications(svc):
    st.markdown("<div class='card'><h3>Notifications</h3></div>", unsafe_allow_html=True)
    notes = svc.notify.list_notifications(DEFAULT_USER_ID)
    if not notes:
        st.info("No notifications")
        return
    for n in notes:
        with st.expander(f"{n.title} — {n.timestamp}"):
            st.write(n.body)
            cols = st.columns([1,1])
            if cols[0].button("Mark read", key=f"mr_{n.notification_id}"):
                svc.notify.mark_read(n.notification_id)
                st.success("Marked read")
            if cols[1].button("Delete", key=f"deln_{n.notification_id}"):
                svc.notify.clear(DEFAULT_USER_ID)
                st.success("Cleared notifications")
    if st.button("Mark all read"):
        svc.notify.mark_all_read(DEFAULT_USER_ID)
        st.success("All marked read")


def page_settings(svc):
    st.markdown("<div class='card'><h3>Settings</h3></div>", unsafe_allow_html=True)
    owner = DEFAULT_USER_ID
    user = svc.storage.get_user(owner)
    if not user:
        st.info("No profile")
        return
    with st.form("profile_form"):
        name = st.text_input("Display name", value=user.display_name)
        country = st.text_input("Country", value=user.country)
        lang = st.text_input("Preferred language", value=user.language)
        save = st.form_submit_button("Save profile")
        if save:
            user.display_name = name
            user.country = country
            user.language = lang
            svc.storage.add_user(user)
            svc.audit.log_event(actor=owner, action="profile_updated", resource=owner, detail="Profile updated", owner_id=owner)
            st.success("Profile updated")
    st.markdown("<h4>Privacy & Behavior</h4>", unsafe_allow_html=True)
    if "require_sensitive_confirmation" not in st.session_state:
        st.session_state["require_sensitive_confirmation"] = True
    st.session_state["require_sensitive_confirmation"] = st.checkbox("Require confirmation for high-sensitivity data", value=st.session_state["require_sensitive_confirmation"])
    if "auto_expire_permissions" not in st.session_state:
        st.session_state["auto_expire_permissions"] = True
    st.session_state["auto_expire_permissions"] = st.checkbox("Automatically expire permissions", value=st.session_state["auto_expire_permissions"])


def page_help_about(svc):
    st.markdown("<div class='card'><h3>About TRUSTPASS</h3></div>", unsafe_allow_html=True)
    st.markdown("""
**TRUSTPASS** — Your Identity. Your Context. Your Permission.

You control what AI can know about you.

TRUSTPASS is a premium-grade user-controlled AI Passport product designed to let individuals manage verified identity and context and selectively authorize AI agents to access specific information. Key features: privacy-first design, granular permissions, field-level consent, revocation, access expiration, and full audit history.

**Important**: This repository is a hackathon product demonstrating TRUSTPASS. It is not an official Egoist Machines product.
""")
    st.markdown("### Brand")
    st.markdown(_logo_html("full"), unsafe_allow_html=True)
