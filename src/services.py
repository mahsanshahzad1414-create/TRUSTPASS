"""
Core service layer for TRUSTPASS
Provides business logic: demo data, credential management, access requests, permissions, audit, notifications, exports, and privacy scoring.
"""
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict
import io
import csv
import json

from .storage import InMemoryStore
from .models import (
    User,
    Credential,
    AIAgent,
    Permission,
    AccessRequest,
    AuditEvent,
    Notification,
    new_id,
    DEFAULT_USER_ID,
    DemoDataConfig,
)
from . import security


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AuditService:
    def __init__(self, storage: InMemoryStore):
        self.storage = storage

    def log_event(self, actor: str, action: str, resource: str, detail: str = "", owner_id: Optional[str] = None, result: str = "ok") -> AuditEvent:
        evt = AuditEvent(event_id=new_id("evt_"), timestamp=utc_now(), actor=actor, action=action, resource=resource, result=result, detail=detail, owner_id=owner_id)
        self.storage.add_audit(evt)
        return evt


class NotificationService:
    def __init__(self, storage: InMemoryStore):
        self.storage = storage

    def notify(self, owner_id: str, title: str, body: str):
        n = Notification(notification_id=new_id("n_"), timestamp=utc_now(), title=title, body=body, owner_id=owner_id, unread=True)
        self.storage.add_notification(n)
        return n

    def list_notifications(self, owner_id: Optional[str] = None):
        return sorted(self.storage.list_notifications(owner_id), key=lambda x: x.timestamp, reverse=True)

    def mark_read(self, notification_id: str):
        self.storage.mark_notification_read(notification_id)

    def mark_all_read(self, owner_id: str):
        self.storage.mark_all_notifications_read(owner_id)

    def clear(self, owner_id: Optional[str] = None):
        self.storage.clear_notifications(owner_id)


class ServiceLayer:
    def __init__(self, storage: InMemoryStore):
        self.storage = storage
        self.audit = AuditService(storage)
        self.notify = NotificationService(storage)

    # Demo data loader
    def load_demo_data(self, config: Optional[DemoDataConfig] = None):
        if config is None:
            config = DemoDataConfig()
        # reset first
        self.storage.reset()
        # user
        user = User(
            user_id=DEFAULT_USER_ID,
            display_name=config.user_name,
            country=config.country,
            language=config.language,
            verified=True,
            passport_number_masked="••••••••4821",
            dob_verified=True,
            last_verified_at=utc_now() - timedelta(days=5),
        )
        self.storage.add_user(user)
        # credentials
        creds = [
            Credential(
                credential_id=new_id("cred_"),
                owner_id=user.user_id,
                name="Bachelor of Computer Science",
                issuer="Nova University",
                type="Degree",
                sensitivity="medium",
                status="Verified",
                issue_date=utc_now() - timedelta(days=365*4),
                expiry_date=None,
            ),
            Credential(
                credential_id=new_id("cred_"),
                owner_id=user.user_id,
                name="GPA Transcript",
                issuer="Nova University",
                type="Academic Record",
                sensitivity="medium",
                status="Verified",
                issue_date=utc_now() - timedelta(days=30),
                expiry_date=None,
            ),
            Credential(
                credential_id=new_id("cred_"),
                owner_id=user.user_id,
                name="IELTS",
                issuer="Language Board",
                type="Language",
                sensitivity="low",
                status="Verified",
                issue_date=utc_now() - timedelta(days=400),
                expiry_date=utc_now() + timedelta(days=365),
            ),
            Credential(
                credential_id=new_id("cred_"),
                owner_id=user.user_id,
                name="Home Address",
                issuer="Self",
                type="Identity",
                sensitivity="high",
                status="Verified",
                issue_date=utc_now() - timedelta(days=1000),
                expiry_date=None,
            ),
        ]
        for c in creds:
            self.storage.add_credential(c)
        # agents
        agents = [
            AIAgent(
                agent_id=new_id("agent_"),
                name="Scholarship AI",
                organization="BrightFuture Foundation",
                description="Assess scholarship eligibility and shortlist candidates.",
                verified=True,
                trust_score=82,
                last_activity=utc_now() - timedelta(minutes=3),
                requested_fields=["Education", "Academic Performance", "English Proficiency", "Passport Number", "Home Address"],
            ),
            AIAgent(
                agent_id=new_id("agent_"),
                name="Career AI",
                organization="HireSmart",
                description="Match candidates to jobs and recommend skill gaps.",
                verified=False,
                trust_score=65,
                last_activity=utc_now() - timedelta(hours=2),
                requested_fields=["Work Experience", "Skills", "Education"],
            ),
            AIAgent(
                agent_id=new_id("agent_"),
                name="Research Assistant AI",
                organization="Atlas AI Labs",
                description="Assist with research paper summarization and literature review.",
                verified=True,
                trust_score=75,
                last_activity=utc_now() - timedelta(days=1, hours=3),
                requested_fields=["Publications", "Education", "Skills"],
            ),
            AIAgent(
                agent_id=new_id("agent_"),
                name="Credential Verification AI",
                organization="Nova Academic Network",
                description="Verify submitted academic credentials against partner records.",
                verified=True,
                trust_score=90,
                last_activity=utc_now() - timedelta(minutes=20),
                requested_fields=["Education", "GPA", "Degree"],
            ),
        ]
        for a in agents:
            self.storage.add_agent(a)
        # pending request example
        req = AccessRequest(
            request_id=new_id("req_"),
            agent_id=agents[0].agent_id,
            owner_id=user.user_id,
            purpose="Determine scholarship eligibility",
            requested_fields=agents[0].requested_fields,
            reason="Apply for BrightFuture undergraduate scholarship",
            requested_duration_hours=168,
        )
        self.storage.add_request(req)
        # active permission example (partial fields)
        perm = Permission(
            permission_id=new_id("perm_"),
            owner_id=user.user_id,
            agent_id=agents[1].agent_id,
            fields=["Work Experience", "Skills"],
            purpose="Job matching",
            granted_at=utc_now() - timedelta(days=2),
            expires_at=utc_now() + timedelta(days=5),
            status="ACTIVE",
            scope="limited",
            note="User-approved for career discovery",
        )
        self.storage.add_permission(perm)
        # revoked permission
        perm2 = Permission(
            permission_id=new_id("perm_"),
            owner_id=user.user_id,
            agent_id=agents[3].agent_id,
            fields=["Education", "GPA"],
            purpose="Credential verification",
            granted_at=utc_now() - timedelta(days=30),
            expires_at=utc_now() - timedelta(days=1),
            status="EXPIRED",
            scope="broad",
            note="Expired auto",
        )
        self.storage.add_permission(perm2)
        # audit events
        self.audit.log_event(actor="system", action="demo_loaded", resource="demo", detail="Demo data populated", owner_id=user.user_id)
        self.notify.notify(owner_id=user.user_id, title="Welcome to TRUSTPASS", body="Your TRUSTPASS demo data is ready. Review pending requests in AI Access Requests.")
        return True

    # Credential operations
    def add_credential(self, owner_id: str, data: dict) -> Credential:
        name = (data.get("name") or "").strip()
        if not name:
            raise ValueError("Credential name is required")
        # duplicate prevention: same name+issuer for owner
        existing = [c for c in self.storage.list_credentials(owner_id) if c.name.lower() == name.lower() and c.issuer.lower() == (data.get("issuer","").lower())]
        if existing:
            raise ValueError("A credential with this name and issuer already exists")
        cred = Credential(
            credential_id=new_id("cred_"),
            owner_id=owner_id,
            name=name,
            issuer=data.get("issuer","Self"),
            type=data.get("type","Other"),
            sensitivity=data.get("sensitivity","low"),
            status=data.get("status","Pending"),
            issue_date=data.get("issue_date"),
            expiry_date=data.get("expiry_date"),
            sharing_allowed=bool(data.get("sharing_allowed", True)),
            notes=data.get("notes",""),
        )
        self.storage.add_credential(cred)
        self.audit.log_event(actor=owner_id, action="credential_added", resource=cred.credential_id, detail=cred.name, owner_id=owner_id)
        self.notify.notify(owner_id=owner_id, title="Credential added", body=f"{cred.name} was added to your passport.")
        return cred

    def edit_credential(self, credential_id: str, updates: dict):
        c = self.storage.get_credential(credential_id)
        if not c:
            raise ValueError("Credential not found")
        for k in ("name","issuer","type","sensitivity","status","notes","sharing_allowed"):
            if k in updates:
                setattr(c, k, updates[k])
        if "issue_date" in updates:
            c.issue_date = updates["issue_date"]
        if "expiry_date" in updates:
            c.expiry_date = updates["expiry_date"]
        self.storage.add_credential(c)
        self.audit.log_event(actor=c.owner_id, action="credential_modified", resource=c.credential_id, detail=c.name, owner_id=c.owner_id)
        self.notify.notify(owner_id=c.owner_id, title="Credential updated", body=f"{c.name} was updated.")
        return c

    def remove_credential(self, credential_id: str, actor: str):
        c = self.storage.get_credential(credential_id)
        if not c:
            raise ValueError("Credential not found")
        self.storage.remove_credential(credential_id)
        self.audit.log_event(actor=actor, action="credential_removed", resource=credential_id, detail=c.name, owner_id=c.owner_id)
        self.notify.notify(owner_id=c.owner_id, title="Credential removed", body=f"{c.name} was removed from your passport.")
        return True

    def verify_credential(self, credential_id: str, actor: str):
        c = self.storage.get_credential(credential_id)
        if not c:
            raise ValueError("Credential not found")
        c.status = "Verified"
        self.storage.add_credential(c)
        self.audit.log_event(actor=actor, action="credential_verified", resource=c.credential_id, detail=c.name, owner_id=c.owner_id)
        self.notify.notify(owner_id=c.owner_id, title="Credential verified", body=f"{c.name} has been verified.")
        return c

    # Requests
    def list_requests(self, owner_id: str) -> List[AccessRequest]:
        return self.storage.list_requests(owner_id)

    def submit_access_request(self, req: AccessRequest):
        self.storage.add_request(req)
        self.audit.log_event(actor=req.agent_id, action="access_requested", resource=req.request_id, detail=req.purpose, owner_id=req.owner_id)
        self.notify.notify(owner_id=req.owner_id, title="New access request", body=f"{req.agent_id} requested access: {req.purpose}")
        return req

    def approve_request(self, request_id: str, approved_fields: List[str], duration_hours: int, approver: str):
        req = self.storage.get_request(request_id)
        if not req:
            raise ValueError("Request not found")
        perm = Permission(
            permission_id=new_id("perm_"),
            owner_id=req.owner_id,
            agent_id=req.agent_id,
            fields=approved_fields,
            purpose=req.purpose,
            granted_at=utc_now(),
            expires_at=(utc_now() + timedelta(hours=duration_hours)) if duration_hours>0 else None,
            status="ACTIVE",
            scope="limited" if len(approved_fields) < len(req.requested_fields) else "broad",
            note=f"Approved via request {request_id}",
        )
        self.storage.add_permission(perm)
        self.storage.mark_request_handled(request_id)
        self.audit.log_event(actor=approver, action="access_approved", resource=perm.permission_id, detail=f"{perm.agent_id}:{perm.fields}", owner_id=req.owner_id)
        self.notify.notify(owner_id=req.owner_id, title="Access granted", body=f"Access granted to {perm.agent_id} for {len(perm.fields)} fields.")
        return perm

    def deny_request(self, request_id: str, actor: str, reason: Optional[str] = None):
        req = self.storage.get_request(request_id)
        if not req:
            raise ValueError("Request not found")
        self.storage.mark_request_handled(request_id)
        self.audit.log_event(actor=actor, action="access_denied", resource=request_id, detail=reason or req.purpose, owner_id=req.owner_id)
        self.notify.notify(owner_id=req.owner_id, title="Access denied", body=f"You denied access request: {req.purpose}")
        return True

    # Permissions
    def list_permissions(self, owner_id: str) -> List[Permission]:
        return self.storage.list_permissions(owner_id)

    def revoke_permission(self, permission_id: str, actor: str, reason: str = ""):
        p = self.storage.get_permission(permission_id)
        if not p:
            raise ValueError("Permission not found")
        p.status = "REVOKED"
        p.expires_at = utc_now()
        self.storage.update_permission(permission_id, p)
        self.audit.log_event(actor=actor, action="permission_revoked", resource=permission_id, detail=reason, owner_id=p.owner_id)
        self.notify.notify(owner_id=p.owner_id, title="Permission revoked", body=f"Access for {p.agent_id} was revoked.")
        return p

    def extend_permission(self, permission_id: str, extra_hours: int, actor: str):
        p = self.storage.get_permission(permission_id)
        if not p:
            raise ValueError("Permission not found")
        if not p.expires_at:
            raise ValueError("Permission has no expiry to extend")
        p.expires_at = p.expires_at + timedelta(hours=extra_hours)
        self.storage.update_permission(permission_id, p)
        self.audit.log_event(actor=actor, action="permission_extended", resource=permission_id, detail=f"extended by {extra_hours}h", owner_id=p.owner_id)
        self.notify.notify(owner_id=p.owner_id, title="Permission extended", body=f"Permission {permission_id} extended by {extra_hours} hours.")
        return p

    def modify_permission_fields(self, permission_id: str, new_fields: List[str], actor: str):
        p = self.storage.get_permission(permission_id)
        if not p:
            raise ValueError("Permission not found")
        old = list(p.fields)
        p.fields = new_fields
        p.scope = "limited" if len(new_fields) < len(old) else p.scope
        self.storage.update_permission(permission_id, p)
        self.audit.log_event(actor=actor, action="permission_modified", resource=permission_id, detail=f"fields changed", owner_id=p.owner_id)
        self.notify.notify(owner_id=p.owner_id, title="Permission modified", body=f"Fields for permission {permission_id} were modified.")
        return p

    def expire_permissions_check(self):
        now = utc_now()
        for p in list(self.storage.permissions.values()):
            if p.status == "ACTIVE" and p.expires_at and p.expires_at <= now:
                p.status = "EXPIRED"
                self.storage.update_permission(p.permission_id, p)
                self.audit.log_event(actor="system", action="permission_expired", resource=p.permission_id, detail="auto-expire", owner_id=p.owner_id)
                self.notify.notify(owner_id=p.owner_id, title="Permission expired", body=f"Permission {p.permission_id} expired.")
        return True

    # Agents
    def list_agents(self) -> List[AIAgent]:
        return self.storage.list_agents()

    # Exports
    def export_audit_csv(self, owner_id: Optional[str] = None) -> bytes:
        events = self.storage.list_audit(owner_id)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["timestamp","actor","action","resource","result","detail","owner_id"])
        for e in events:
            writer.writerow([e.timestamp.isoformat(), e.actor, e.action, e.resource, e.result, (e.detail or ""), e.owner_id or ""])
        return output.getvalue().encode("utf-8")

    def export_permissions_csv(self, owner_id: str) -> bytes:
        perms = self.list_permissions(owner_id)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["permission_id","agent_id","fields","purpose","granted_at","expires_at","status","scope","note"])
        for p in perms:
            writer.writerow([p.permission_id, p.agent_id, ";".join(p.fields), p.purpose, p.granted_at.isoformat(), p.expires_at.isoformat() if p.expires_at else "", p.status, p.scope, p.note])
        return output.getvalue().encode("utf-8")

    def export_credentials_csv(self, owner_id: str) -> bytes:
        creds = self.storage.list_credentials(owner_id)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["credential_id","name","issuer","type","sensitivity","status","issue_date","expiry_date","sharing_allowed","notes"])
        for c in creds:
            writer.writerow([c.credential_id, c.name, c.issuer, c.type, c.sensitivity, c.status, c.issue_date.isoformat() if c.issue_date else "", c.expiry_date.isoformat() if c.expiry_date else "", c.sharing_allowed, c.notes])
        return output.getvalue().encode("utf-8")

    def export_passport_json(self, owner_id: str) -> bytes:
        user = self.storage.get_user(owner_id)
        if not user:
            return b"{}"
        # include public user fields and metadata only
        creds = []
        for c in self.storage.list_credentials(owner_id):
            creds.append({
                "credential_id": c.credential_id,
                "name": c.name,
                "issuer": c.issuer,
                "type": c.type,
                "sensitivity": c.sensitivity,
                "status": c.status,
                "issue_date": c.issue_date.isoformat() if c.issue_date else None,
                "expiry_date": c.expiry_date.isoformat() if c.expiry_date else None,
                "sharing_allowed": c.sharing_allowed,
                "notes": c.notes,
            })
        perms = []
        for p in self.list_permissions(owner_id):
            perms.append({
                "permission_id": p.permission_id,
                "agent_id": p.agent_id,
                "fields": p.fields,
                "purpose": p.purpose,
                "granted_at": p.granted_at.isoformat(),
                "expires_at": p.expires_at.isoformat() if p.expires_at else None,
                "status": p.status,
                "scope": p.scope,
            })
        obj = {"user": user.to_public(), "credentials": creds, "permissions": perms}
        return json.dumps(obj, default=str, indent=2).encode("utf-8")

    # Privacy & risk helpers
    def classify_field(self, field: str) -> str:
        f = (field or "").lower()
        high = ["passport","passport number","home address","date of birth","government id","ssn"]
        medium = ["gpa","academic","degree","work","work experience","salary","employment"]
        low = ["skills","language","education","publications"]
        if any(h in f for h in high):
            return "high"
        if any(m in f for m in medium):
            return "medium"
        return "low"

    def recommend_minimum_fields(self, requested_fields: List[str]) -> List[str]:
        # naive heuristic: exclude high-sensitivity fields unless they are the only field
        rec = [f for f in requested_fields if self.classify_field(f) != "high"]
        if not rec and requested_fields:
            return [requested_fields[0]]
        return rec

    def risk_assessment(self, requested_fields: List[str], agent: Optional[AIAgent] = None) -> Dict:
        by_sens = {"high":[],"medium":[],"low":[]}
        score = 0
        for f in requested_fields:
            s = self.classify_field(f)
            by_sens[s].append(f)
            if s=="high":
                score += 30
            elif s=="medium":
                score += 10
        if agent and not agent.verified:
            score += 10
        # short duration reduces risk—handled elsewhere
        level = "Low"
        if score >=50:
            level = "High"
        elif score >=20:
            level = "Medium"
        return {"by_sensitivity": by_sens, "score": score, "level": level}

    # Privacy scoring functions
    def compute_passport_health(self, owner_id: str) -> Dict:
        user = self.storage.get_user(owner_id)
        creds = self.storage.list_credentials(owner_id)
        verified_creds = len([c for c in creds if c.status=="Verified"])
        total_creds = len(creds)
        perms = self.list_permissions(owner_id)
        active_broad = len([p for p in perms if p.status=="ACTIVE" and p.scope=="broad"]) 
        active_agents = len(set([p.agent_id for p in perms if p.status=="ACTIVE"]))
        expired = len([p for p in perms if p.status=="EXPIRED"])
        score = 40
        score += 20 if user and user.verified else 0
        if total_creds>0:
            score += min(20, int(20*(verified_creds/total_creds)))
        score -= min(30, active_broad*6 + active_agents*2)
        if expired>0:
            score -= 10
        score = max(0, min(100, score))
        breakdown = {
            "base":40,
            "verified_user":20 if user and user.verified else 0,
            "credential_completeness": min(20, int(20*(verified_creds/total_creds))) if total_creds>0 else 0,
            "broad_permission_penalty": min(30, active_broad*6 + active_agents*2),
            "expired_penalty": 10 if expired>0 else 0,
        }
        return {"score":score, "breakdown":breakdown}

    def compute_privacy_score(self, owner_id: str) -> Dict:
        creds = self.storage.list_credentials(owner_id)
        total_fields = max(1, len(creds)*3)  # approximate: assume 3 fields per credential
        perms = self.list_permissions(owner_id)
        active_perms = [p for p in perms if p.status=="ACTIVE"]
        shared_fields = sum(len(p.fields) for p in active_perms)
        high_shared = 0
        for p in active_perms:
            for f in p.fields:
                if self.classify_field(f)=="high":
                    high_shared +=1
        broad = len([p for p in active_perms if p.scope=="broad"])
        minimization = max(0, 1 - (shared_fields / total_fields)) * 100
        penalty = min(90, high_shared*10 + broad*7)
        score = max(0, int(minimization - penalty))
        details = {"total_fields":total_fields, "shared_fields":shared_fields, "high_shared":high_shared, "broad_permissions":broad}
        return {"score":score, "details":details}
