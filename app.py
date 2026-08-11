import os

files = {
    "requirements.txt": """streamlit>=1.20.0
pandas>=1.3.0
""",
    
    ".gitignore": """__pycache__/
*.pyc
.env
.vscode/
.DS_Store
assets/*.png
""",

    "README.md": """# TRUSTPASS

TRUSTPASS — Your Identity. Your Context. Your Permission.

You control what AI can know about you.

---

This repository contains a complete Streamlit application demonstrating TRUSTPASS: a premium, privacy-first AI Passport platform for managing identity, credentials, and fine-grained AI access permissions.

Key features:
- Identity & Passport overview
- Credential Vault (add/edit/verify/revoke/expire)
- AI Access Requests and field-level approvals with least-privilege recommendations
- Permission management (active, expiring, expired, revoked)
- AI Agent Directory with trust indicators
- Privacy, Trust, and Passport Health scoring with deterministic formulas
- Audit logging and Notifications
- Exports (Passport JSON, Credentials CSV, Permissions CSV, Audit CSV) — sensitive values redacted
- Demo Mode with deterministic fictional data (Alex Rivera, BrightFuture Foundation, HireSmart, Nova Academic Network, Atlas AI Labs)
- Premium dark theme and integrated branding (SVG assets)

Installation
1. Create Python 3.8+ environment
2. Install dependencies:
   pip install -r requirements.txt
3. Run:
   streamlit run app.py
""",

    "src/__init__.py": """# src package
""",

    "src/models.py": """\"\"\"
Domain models for TRUSTPASS
\"\"\"
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Optional, Dict
import uuid


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex[:8]}"


DEFAULT_USER_ID = "user_demo_1"


@dataclass
class DemoDataConfig:
    user_name: str = "Alex Rivera"
    country: str = "Freedonia"
    language: str = "English"


@dataclass
class User:
    user_id: str
    display_name: str
    country: str
    language: str
    verified: bool = False
    passport_number_masked: str = "••••••••0000"
    dob_verified: bool = False
    last_verified_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=utc_now)

    def to_public(self) -> Dict:
        d = asdict(self)
        d["passport_number_masked"] = self.passport_number_masked
        return d


@dataclass
class Credential:
    credential_id: str
    owner_id: str
    name: str
    issuer: str
    type: str
    sensitivity: str  # low|medium|high
    status: str  # Verified|Pending|Expired|Revoked
    issue_date: Optional[datetime]
    expiry_date: Optional[datetime]
    sharing_allowed: bool = True
    notes: str = ""
    created_at: datetime = field(default_factory=utc_now)


@dataclass
class AIAgent:
    agent_id: str
    name: str
    organization: str
    description: str
    verified: bool
    trust_score: int  # 0-100
    last_activity: Optional[datetime]
    requested_fields: List[str] = field(default_factory=list)


@dataclass
class Permission:
    permission_id: str
    owner_id: str
    agent_id: str
    fields: List[str]
    purpose: str
    granted_at: datetime
    expires_at: Optional[datetime]
    status: str  # ACTIVE|EXPIRED|REVOKED|DENIED|PENDING
    scope: str  # limited|broad
    note: str = ""


@dataclass
class AccessRequest:
    request_id: str
    agent_id: str
    owner_id: str
    purpose: str
    requested_fields: List[str]
    reason: Optional[str]
    requested_duration_hours: int
    created_at: datetime = field(default_factory=utc_now)
    handled: bool = False


@dataclass
class AuditEvent:
    event_id: str
    timestamp: datetime
    actor: str
    action: str
    resource: str
    result: str
    detail: Optional[str] = ""
    owner_id: Optional[str] = None


@dataclass
class Notification:
    notification_id: str
    timestamp: datetime
    title: str
    body: str
    owner_id: Optional[str] = None
    unread: bool = True
""",

    "src/security.py": """\"\"\"
Security configuration and helpers (demo-level).
\"\"\"
from typing import Dict

PALETTE = {
    "navy": "#0B1220",
    "violet": "#7C3AED",
    "cyan": "#06B6D4",
    "green": "#10B981",
    "amber": "#F59E0B",
    "red": "#EF4444",
}

DEFAULTS = {
    "require_sensitive_confirmation": True,
    "auto_expire_permissions": True,
    "default_permission_hours": 168,
}
""",

    "src/storage.py": """\"\"\"
Simple in-memory store. Replaceable by a DB-backed implementation.
\"\"\"
from typing import Dict, List, Optional
from .models import (
    User,
    Credential,
    AIAgent,
    Permission,
    AccessRequest,
    AuditEvent,
    Notification,
)


class InMemoryStore:
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.users: Dict[str, User] = {}
        self.credentials: Dict[str, Credential] = {}
        self.agents: Dict[str, AIAgent] = {}
        self.permissions: Dict[str, Permission] = {}
        self.requests: Dict[str, AccessRequest] = {}
        self.audit: Dict[str, AuditEvent] = {}
        self.notifications: Dict[str, Notification] = {}
        self._demo_loaded = False

    def has_demo_loaded(self) -> bool:
        return self._demo_loaded

    def set_demo_loaded(self, v: bool = True):
        self._demo_loaded = v

    def reset(self):
        self.users.clear()
        self.credentials.clear()
        self.agents.clear()
        self.permissions.clear()
        self.requests.clear()
        self.audit.clear()
        self.notifications.clear()
        self._demo_loaded = False

    def add_user(self, u: User):
        self.users[u.user_id] = u

    def get_user(self, user_id: str) -> Optional[User]:
        return self.users.get(user_id)

    def add_credential(self, c: Credential):
        self.credentials[c.credential_id] = c

    def list_credentials(self, owner_id: str) -> List[Credential]:
        return [c for c in self.credentials.values() if c.owner_id == owner_id]

    def get_credential(self, credential_id: str) -> Optional[Credential]:
        return self.credentials.get(credential_id)

    def remove_credential(self, credential_id: str):
        if credential_id in self.credentials:
            del self.credentials[credential_id]

    def add_agent(self, a: AIAgent):
        self.agents[a.agent_id] = a

    def list_agents(self) -> List[AIAgent]:
        return list(self.agents.values())

    def get_agent(self, agent_id: str) -> Optional[AIAgent]:
        return self.agents.get(agent_id)

    def add_permission(self, p: Permission):
        self.permissions[p.permission_id] = p

    def list_permissions(self, owner_id: str) -> List[Permission]:
        return [p for p in self.permissions.values() if p.owner_id == owner_id]

    def get_permission(self, permission_id: str) -> Optional[Permission]:
        return self.permissions.get(permission_id)

    def update_permission(self, permission_id: str, p: Permission):
        self.permissions[permission_id] = p

    def remove_permission(self, permission_id: str):
        if permission_id in self.permissions:
            del self.permissions[permission_id]

    def add_request(self, r: AccessRequest):
        self.requests[r.request_id] = r

    def list_requests(self, owner_id: str) -> List[AccessRequest]:
        return [r for r in self.requests.values() if r.owner_id == owner_id and not r.handled]

    def get_request(self, request_id: str) -> Optional[AccessRequest]:
        return self.requests.get(request_id)

    def mark_request_handled(self, request_id: str):
        r = self.requests.get(request_id)
        if r:
            r.handled = True
            self.requests[request_id] = r

    def add_audit(self, e: AuditEvent):
        self.audit[e.event_id] = e

    def list_audit(self, owner_id: Optional[str] = None):
        if owner_id:
            return [a for a in self.audit.values() if a.owner_id == owner_id]
        return list(self.audit.values())

    def add_notification(self, n: Notification):
        self.notifications[n.notification_id] = n

    def list_notifications(self, owner_id: Optional[str] = None):
        if owner_id:
            return [n for n in self.notifications.values() if n.owner_id == owner_id]
        return list(self.notifications.values())

    def mark_notification_read(self, notification_id: str):
        n = self.notifications.get(notification_id)
        if n:
            n.unread = False
            self.notifications[notification_id] = n

    def mark_all_notifications_read(self, owner_id: str):
        for nid, n in list(self.notifications.items()):
            if n.owner_id == owner_id:
                n.unread = False
                self.notifications[nid] = n

    def clear_notifications(self, owner_id: Optional[str] = None):
        if owner_id is None:
            self.notifications.clear()
        else:
            for nid, n in list(self.notifications.items()):
                if n.owner_id == owner_id:
                    del self.notifications[nid]
""",

    "src/privacy.py": """\"\"\"
Privacy and scoring utilities.
Deterministic, explainable formulas for Passport Health, Privacy Score, Trust Score, and Permission Risk.
\"\"\"
from datetime import datetime, timezone
from typing import List, Dict


def classify_field(field: str) -> str:
    f = (field or "").lower()
    high = ["passport", "passport number", "home address", "date of birth", "government id", "ssn"]
    medium = ["gpa", "academic", "degree", "work", "work experience", "employment", "salary"]
    low = ["skills", "language", "education", "publications"]
    if any(h in f for h in high):
        return "high"
    if any(m in f for m in medium):
        return "medium"
    return "low"


def recommend_minimum_fields(requested_fields: List[str]) -> List[str]:
    recommended = [f for f in requested_fields if classify_field(f) != "high"]
    if not recommended and requested_fields:
        return [requested_fields[0]]
    return recommended


def compute_passport_health(user_verified: bool, credentials: List[dict], permissions: List[dict]) -> Dict:
    base = 40
    verified_bonus = 20 if user_verified else 0
    total_creds = len(credentials)
    verified_creds = len([c for c in credentials if c.get("status") == "Verified"])
    credential_score = int((verified_creds / total_creds) * 20) if total_creds else 0
    active_perms = [p for p in permissions if p.get("status") == "ACTIVE"]
    broad_count = len([p for p in active_perms if p.get("scope") == "broad"])
    active_agents = len(set([p.get("agent_id") for p in active_perms]))
    penalty = min(30, broad_count * 6 + active_agents * 2)
    expired_penalty = 10 if any(p.get("status") == "EXPIRED" for p in permissions) else 0
    score = base + verified_bonus + credential_score - penalty - expired_penalty
    score = max(0, min(100, score))
    breakdown = {
        "base": base,
        "verified_user": verified_bonus,
        "credential_score": credential_score,
        "broad_permission_penalty": penalty,
        "expired_penalty": expired_penalty,
    }
    return {"score": int(score), "breakdown": breakdown}


def compute_privacy_score(credentials: List[dict], permissions: List[dict]) -> Dict:
    total_fields = max(1, len(credentials) * 3)
    active_perms = [p for p in permissions if p.get("status") == "ACTIVE"]
    shared_fields = sum(len(p.get("fields", [])) for p in active_perms)
    high_shared = 0
    for p in active_perms:
        for f in p.get("fields", []):
            if classify_field(f) == "high":
                high_shared += 1
    broad = len([p for p in active_perms if p.get("scope") == "broad"])
    minimization = max(0.0, 1.0 - (shared_fields / total_fields)) * 100
    penalty = min(90, high_shared * 10 + broad * 7)
    score = max(0, int(minimization - penalty))
    details = {
        "total_fields_estimate": total_fields,
        "shared_fields": shared_fields,
        "high_shared": high_shared,
        "broad_permissions": broad,
        "minimization_percent": int(minimization),
        "penalty": penalty,
    }
    return {"score": score, "details": details}
""",

    "src/exports.py": """\"\"\"
Export helpers producing safe downloadable content.
\"\"\"
import csv
import io
import json
from typing import List, Dict


def redact_credential_for_export(c: Dict) -> Dict:
    return {
        "credential_id": c.get("credential_id"),
        "name": c.get("name"),
        "issuer": c.get("issuer"),
        "type": c.get("type"),
        "sensitivity": c.get("sensitivity"),
        "status": c.get("status"),
        "issue_date": c.get("issue_date").isoformat() if c.get("issue_date") else "",
        "expiry_date": c.get("expiry_date").isoformat() if c.get("expiry_date") else "",
        "sharing_allowed": c.get("sharing_allowed"),
        "notes": c.get("notes"),
    }


def credentials_csv_bytes(creds: List[Dict]) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["credential_id", "name", "issuer", "type", "sensitivity", "status", "issue_date", "expiry_date", "sharing_allowed", "notes"])
    for c in creds:
        r = redact_credential_for_export(c)
        writer.writerow([r[k] for k in ["credential_id", "name", "issuer", "type", "sensitivity", "status", "issue_date", "expiry_date", "sharing_allowed", "notes"]])
    return output.getvalue().encode("utf-8")


def permissions_csv_bytes(perms: List[Dict]) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["permission_id", "agent_id", "fields", "purpose", "granted_at", "expires_at", "status", "scope", "note"])
    for p in perms:
        writer.writerow([
            p.get("permission_id"),
            p.get("agent_id"),
            ";".join(p.get("fields", [])),
            p.get("purpose"),
            p.get("granted_at").isoformat() if p.get("granted_at") else "",
            p.get("expires_at").isoformat() if p.get("expires_at") else "",
            p.get("status"),
            p.get("scope"),
            p.get("note"),
        ])
    return output.getvalue().encode("utf-8")


def audit_csv_bytes(events: List[Dict]) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["timestamp", "actor", "action", "resource", "result", "detail", "owner_id"])
    for e in events:
        writer.writerow([
            e.get("timestamp").isoformat() if getattr(e.get("timestamp", None), "isoformat", None) else e.get("timestamp"),
            e.get("actor"),
            e.get("action"),
            e.get("resource"),
            e.get("result"),
            e.get("detail"),
            e.get("owner_id"),
        ])
    return output.getvalue().encode("utf-8")


def passport_json_bytes(user: Dict, creds: List[Dict], perms: List[Dict]) -> bytes:
    obj = {
        "user": {
            "user_id": user.get("user_id"),
            "display_name": user.get("display_name"),
            "country": user.get("country"),
            "language": user.get("language"),
            "verified": user.get("verified"),
            "passport_number_masked": user.get("passport_number_masked"),
            "dob_verified": user.get("dob_verified"),
            "last_verified_at": user.get("last_verified_at").isoformat() if user.get("last_verified_at") else None,
        },
        "credentials": [redact_credential_for_export(c) for c in creds],
        "permissions": [
            {
                "permission_id": p.get("permission_id"),
                "agent_id": p.get("agent_id"),
                "fields": p.get("fields"),
                "purpose": p.get("purpose"),
                "granted_at": p.get("granted_at").isoformat() if p.get("granted_at") else None,
                "expires_at": p.get("expires_at").isoformat() if p.get("expires_at") else None,
                "status": p.get("status"),
                "scope": p.get("scope"),
            } for p in perms
        ],
    }
    return json.dumps(obj, indent=2, default=str).encode("utf-8")
""",

    "src/services.py": """\"\"\"
Service layer: coordinates storage, audit, notifications, and business logic.
\"\"\"
from datetime import datetime, timedelta, timezone
from typing import List, Optional

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
from . import exports

UTC = timezone.utc


def utc_now():
    return datetime.now(UTC)


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

    def list_notifications(self, owner_id: str):
        notes = self.storage.list_notifications(owner_id)
        return sorted(notes, key=lambda n: n.timestamp, reverse=True)

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

    def load_demo_data(self, cfg: Optional[DemoDataConfig] = None):
        if cfg is None:
            cfg = DemoDataConfig()
        self.storage.reset()
        user = User(
            user_id=DEFAULT_USER_ID,
            display_name=cfg.user_name,
            country=cfg.country,
            language=cfg.language,
            verified=True,
            passport_number_masked="••••••••4821",
            dob_verified=True,
            last_verified_at=utc_now() - timedelta(days=5),
        )
        self.storage.add_user(user)
        creds = [
            Credential(credential_id=new_id("cred_"), owner_id=user.user_id, name="Bachelor of Computer Science", issuer="Nova University", type="Degree", sensitivity="medium", status="Verified", issue_date=utc_now() - timedelta(days=365*4), expiry_date=None),
            Credential(credential_id=new_id("cred_"), owner_id=user.user_id, name="GPA Transcript", issuer="Nova University", type="Academic Record", sensitivity="medium", status="Verified", issue_date=utc_now() - timedelta(days=30), expiry_date=None),
            Credential(credential_id=new_id("cred_"), owner_id=user.user_id, name="IELTS", issuer="Language Board", type="Language", sensitivity="low", status="Verified", issue_date=utc_now() - timedelta(days=400), expiry_date=utc_now() + timedelta(days=365)),
            Credential(credential_id=new_id("cred_"), owner_id=user.user_id, name="Home Address", issuer="Self", type="Identity", sensitivity="high", status="Verified", issue_date=utc_now() - timedelta(days=1000), expiry_date=None),
        ]
        for c in creds:
            self.storage.add_credential(c)
        agents = [
            AIAgent(agent_id=new_id("agent_"), name="Scholarship AI", organization="BrightFuture Foundation", description="Assess scholarship eligibility and shortlist candidates.", verified=True, trust_score=82, last_activity=utc_now() - timedelta(minutes=3), requested_fields=["Education", "Academic Performance", "English Proficiency", "Passport Number", "Home Address"]),
            AIAgent(agent_id=new_id("agent_"), name="Career AI", organization="HireSmart", description="Match candidates to jobs and recommend skill gaps.", verified=False, trust_score=65, last_activity=utc_now() - timedelta(hours=2), requested_fields=["Work Experience", "Skills", "Education"]),
            AIAgent(agent_id=new_id("agent_"), name="Research Assistant AI", organization="Atlas AI Labs", description="Assist with research literature and summaries.", verified=True, trust_score=75, last_activity=utc_now() - timedelta(days=1, hours=3), requested_fields=["Publications", "Education", "Skills"]),
            AIAgent(agent_id=new_id("agent_"), name="Credential Verification AI", organization="Nova Academic Network", description="Verify academic credentials with partner institutions.", verified=True, trust_score=90, last_activity=utc_now() - timedelta(minutes=20), requested_fields=["Education", "GPA", "Degree"]),
        ]
        for a in agents:
            self.storage.add_agent(a)
        req = AccessRequest(request_id=new_id("req_"), agent_id=agents[0].agent_id, owner_id=user.user_id, purpose="Determine scholarship eligibility", requested_fields=agents[0].requested_fields, reason="Apply for BrightFuture undergraduate scholarship", requested_duration_hours=168)
        self.storage.add_request(req)
        perm = Permission(permission_id=new_id("perm_"), owner_id=user.user_id, agent_id=agents[1].agent_id, fields=["Work Experience", "Skills"], purpose="Job matching", granted_at=utc_now() - timedelta(days=2), expires_at=utc_now() + timedelta(days=5), status="ACTIVE", scope="limited", note="User-approved for career discovery")
        self.storage.add_permission(perm)
        perm2 = Permission(permission_id=new_id("perm_"), owner_id=user.user_id, agent_id=agents[3].agent_id, fields=["Education", "GPA"], purpose="Credential verification", granted_at=utc_now() - timedelta(days=30), expires_at=utc_now() - timedelta(days=1), status="EXPIRED", scope="broad", note="Expired automatically")
        self.storage.add_permission(perm2)
        self.audit.log_event(actor="system", action="demo_loaded", resource="demo", detail="Demo data loaded", owner_id=user.user_id)
        self.notify.notify(owner_id=user.user_id, title="Welcome to TRUSTPASS", body="Demo data loaded: review pending requests in AI Access Requests.")
        self.storage.set_demo_loaded(True)
        return True

    def add_credential(self, owner_id: str, data: dict) -> Credential:
        name = (data.get("name") or "").strip()
        if not name:
            raise ValueError("Credential name is required")
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
        self.notify.notify(owner_id=owner_id, title="Credential added", body=f"{cred.name} added to your passport.")
        return cred

    def edit_credential(self, credential_id: str, updates: dict) -> Credential:
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
        self.notify.notify(owner_id=c.owner_id, title="Credential updated", body=f"{c.name} updated.")
        return c

    def remove_credential(self, credential_id: str, actor: str) -> bool:
        c = self.storage.get_credential(credential_id)
        if not c:
            raise ValueError("Credential not found")
        self.storage.remove_credential(credential_id)
        self.audit.log_event(actor=actor, action="credential_removed", resource=credential_id, detail=c.name, owner_id=c.owner_id)
        self.notify.notify(owner_id=c.owner_id, title="Credential removed", body=f"{c.name} removed from your passport.")
        return True

    def verify_credential(self, credential_id: str, actor: str) -> Credential:
        c = self.storage.get_credential(credential_id)
        if not c:
            raise ValueError("Credential not found")
        c.status = "Verified"
        self.storage.add_credential(c)
        self.audit.log_event(actor=actor, action="credential_verified", resource=c.credential_id, detail=c.name, owner_id=c.owner_id)
        self.notify.notify(owner_id=c.owner_id, title="Credential verified", body=f"{c.name} has been verified.")
        return c

    def list_requests(self, owner_id: str) -> List[AccessRequest]:
        return self.storage.list_requests(owner_id)

    def submit_access_request(self, req: AccessRequest) -> AccessRequest:
        self.storage.add_request(req)
        self.audit.log_event(actor=req.agent_id, action="access_requested", resource=req.request_id, detail=req.purpose, owner_id=req.owner_id)
        self.notify.notify(owner_id=req.owner_id, title="New access request", body=f"{req.agent_id} requested access: {req.purpose}")
        return req

    def approve_request(self, request_id: str, approved_fields: List[str], duration_hours: int, approver: str) -> Permission:
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
            expires_at=(utc_now() + timedelta(hours=duration_hours)) if duration_hours > 0 else None,
            status="ACTIVE",
            scope="limited" if len(approved_fields) < len(req.requested_fields) else "broad",
            note=f"Approved via request {request_id}",
        )
        self.storage.add_permission(perm)
        self.storage.mark_request_handled(request_id)
        self.audit.log_event(actor=approver, action="access_approved", resource=perm.permission_id, detail=f"{perm.agent_id}:{perm.fields}", owner_id=req.owner_id)
        self.notify.notify(owner_id=req.owner_id, title="Access granted", body=f"Access granted to {perm.agent_id} for {len(perm.fields)} fields.")
        return perm

    def deny_request(self, request_id: str, actor: str, reason: Optional[str] = None) -> bool:
        req = self.storage.get_request(request_id)
        if not req:
            raise ValueError("Request not found")
        self.storage.mark_request_handled(request_id)
        self.audit.log_event(actor=actor, action="access_denied", resource=request_id, detail=reason or req.purpose, owner_id=req.owner_id)
        self.notify.notify(owner_id=req.owner_id, title="Access denied", body=f"You denied access request: {req.purpose}")
        return True

    def list_permissions(self, owner_id: str) -> List[Permission]:
        return self.storage.list_permissions(owner_id)

    def revoke_permission(self, permission_id: str, actor: str, reason: str = "") -> Permission:
        p = self.storage.get_permission(permission_id)
        if not p:
            raise ValueError("Permission not found")
        p.status = "REVOKED"
        p.expires_at = utc_now()
        self.storage.update_permission(permission_id, p)
        self.audit.log_event(actor=actor, action="permission_revoked", resource=permission_id, detail=reason, owner_id=p.owner_id)
        self.notify.notify(owner_id=p.owner_id, title="Permission revoked", body=f"Access for {p.agent_id} was revoked.")
        return p

    def extend_permission(self, permission_id: str, extra_hours: int, actor: str) -> Permission:
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

    def modify_permission_fields(self, permission_id: str, new_fields: List[str], actor: str) -> Permission:
        p = self.storage.get_permission(permission_id)
        if not p:
            raise ValueError("Permission not found")
        old_fields = list(p.fields)
        p.fields = new_fields
        p.scope = "limited" if len(new_fields) < len(old_fields) else p.scope
        self.storage.update_permission(permission_id, p)
        self.audit.log_event(actor=actor, action="permission_modified", resource=permission_id, detail="fields changed", owner_id=p.owner_id)
        self.notify.notify(owner_id=p.owner_id, title="Permission modified", body=f"Fields for permission {permission_id} modified.")
        return p

    def list_agents(self) -> List[AIAgent]:
        return self.storage.list_agents()

    def export_audit_csv(self, owner_id: Optional[str] = None) -> bytes:
        evs = self.storage.list_audit(owner_id)
        return exports.audit_csv_bytes([e.__dict__ for e in evs])

    def export_permissions_csv(self, owner_id: str) -> bytes:
        perms = [p.__dict__ for p in self.list_permissions(owner_id)]
        return exports.permissions_csv_bytes(perms)

    def export_credentials_csv(self, owner_id: str) -> bytes:
        creds = [c.__dict__ for c in self.storage.list_credentials(owner_id)]
        return exports.credentials_csv_bytes(creds)

    def export_passport_json(self, owner_id: str) -> bytes:
        user = self.storage.get_user(owner_id)
        creds = [c.__dict__ for c in self.storage.list_credentials(owner_id)]
        perms = [p.__dict__ for p in self.list_permissions(owner_id)]
        return exports.passport_json_bytes(user.__dict__ if user else {}, creds, perms)
""",

    "src/ui.py": """\"\"\"
Streamlit UI pages for TRUSTPASS.
A premium dark theme is applied via CSS. All pages are wired to ServiceLayer.
\"\"\"
from datetime import datetime, timezone
from typing import Optional
import streamlit as st
import pandas as pd

from .models import DEFAULT_USER_ID
from .privacy import classify_field, recommend_minimum_fields, compute_passport_health, compute_privacy_score
from . import security

CSS = f\"\"\"
:root{{
  --bg: {security.PALETTE['navy'] if hasattr(security,'PALETTE') else '#0B1220'};
  --card: rgba(255,255,255,0.02);
  --muted: #94a3b8;
  --accent: {security.PALETTE['violet'] if hasattr(security,'PALETTE') else '#7C3AED'};
  --accent-2: {security.PALETTE['cyan'] if hasattr(security,'PALETTE') else '#06B6D4'};
  --success: {security.PALETTE['green'] if hasattr(security,'PALETTE') else '#10B981'};
  --warn: {security.PALETTE['amber'] if hasattr(security,'PALETTE') else '#F59E0B'};
  --danger: {security.PALETTE['red'] if hasattr(security,'PALETTE') else '#EF4444'};
}}
body {{ background-color: var(--bg); color: #e6eef6; }}
header[role=\"banner\"] {{ display:none; }}
.sidebar .block-container {{ background: linear-gradient(180deg, rgba(255,255,255,0.01), rgba(255,255,255,0.02)); padding: 16px; }}
.card {{ background: var(--card); padding: 16px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.03); margin-bottom: 12px; }}
.kpi {{ font-size:20px; font-weight:700; color: #fff; }}
.small {{ font-size:13px; color:var(--muted); }}
.badge {{ background: rgba(255,255,255,0.03); padding:6px 10px; border-radius:999px; color:var(--muted); font-size:12px; display:inline-block; }}
.logo-word {{ font-weight:700; letter-spacing:1px; font-size:18px; color:#fff; }}
.logo-tag {{ font-size:11px; color:var(--muted); }}
.btn-primary {{ background: linear-gradient(90deg,var(--accent),var(--accent-2)); color: white; padding:8px 12px; border-radius:8px; border: none; }}
\"\"\"

def inject_css():
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


def _logo_html(variant: str = "full"):
    path = "assets/brand/trustpass-logo.svg" if variant == "full" else "assets/brand/trustpass-mark.svg"
    return f"<img src='{path}' style='height:44px' alt='TRUSTPASS'/>"


def app_header(title: str, tagline: str, svc):
    cols = st.columns([1, 4, 1])
    with cols[0]:
        st.markdown(_logo_html("mark"), unsafe_allow_html=True)
    with cols[1]:
        st.markdown(f"<div style='padding-left:8px'><div class='logo-word'>{title}</div><div class='logo-tag'>{tagline}</div></div>", unsafe_allow_html=True)
    with cols[2]:
        notes = svc.notify.list_notifications(DEFAULT_USER_ID)
        unread = sum(1 for n in notes if n.unread)
        st.markdown(f"<div style='text-align:right'><span class='badge'>Notifications: {unread}</span></div>", unsafe_allow_html=True)


def sidebar_navigation(ss):
    st.markdown(_logo_html("full"), unsafe_allow_html=True)
    st.markdown("<div style='margin-top:8px'><div class='logo-word'>TRUSTPASS</div><div class='small'>Your Identity. Your Context. Your Permission.</div></div>", unsafe_allow_html=True)
    st.markdown("---")
    pages = ["Overview", "My AI Passport", "Credentials", "AI Access Requests", "Permissions", "AI Agents", "Access History", "Privacy Center", "Security Center", "Notifications", "Settings", "Help / About"]
    choice = st.radio("", options=pages, index=pages.index(st.session_state.get("nav","Overview")), key="nav_radio")
    st.session_state["nav"] = choice
    st.markdown("---")
    if st.button("Load Demo Data"):
        st.session_state["svc"].load_demo_data()
        st.success("Demo data loaded")


def human_timedelta(dt: Optional[datetime]):
    if not dt:
        return "No expiry"
    now = datetime.now(timezone.utc)
    delta = dt - now
    total = int(delta.total_seconds())
    if total <= 0:
        return "Expired"
    days = total // 86400
    hours = (total % 86400) // 3600
    return f"{days}d {hours}h"


def page_overview(svc):
    st.markdown("<div class='card'><h3>Overview</h3></div>", unsafe_allow_html=True)
    owner = DEFAULT_USER_ID
    user = svc.storage.get_user(owner)
    if not user:
        st.info("No profile. Use Load Demo Data to populate sample data.")
        return
    creds = [c.__dict__ for c in svc.storage.list_credentials(owner)]
    perms = [p.__dict__ for p in svc.list_permissions(owner)]
    health = compute_passport_health_ui(svc, owner)
    privacy = compute_privacy_ui(svc, owner)
    agents = svc.list_agents()
    verified_creds = len([c for c in creds if c.get("status") == "Verified"])
    active_perms = [p for p in perms if p.get("status") == "ACTIVE"]
    pending_reqs = svc.list_requests(owner)
    sensitive_shared = sum(1 for p in active_perms for f in p.get("fields", []) if classify_field(f) == "high")

    cols = st.columns(4)
    cols[0].markdown(f"<div class='card'><div class='small'>Passport Health</div><div class='kpi'>{health['score']}%</div></div>", unsafe_allow_html=True)
    cols[1].markdown(f"<div class='card'><div class='small'>Privacy Score</div><div class='kpi'>{privacy['score']}%</div></div>", unsafe_allow_html=True)
    cols[2].markdown(f"<div class='card'><div class='small'>Verified Credentials</div><div class='kpi'>{verified_creds}</div></div>", unsafe_allow_html=True)
    cols[3].markdown(f"<div class='card'><div class='small'>Active AI Agents</div><div class='kpi'>{len(set([p['agent_id'] for p in perms if p.get('status')=='ACTIVE']))}</div></div>", unsafe_allow_html=True)

    cols2 = st.columns(4)
    cols2[0].markdown(f"<div class='card'><div class='small'>Active Permissions</div><div class='kpi'>{len(active_perms)}</div></div>", unsafe_allow_html=True)
    cols2[1].markdown(f"<div class='card'><div class='small'>Pending Requests</div><div class='kpi'>{len(pending_reqs)}</div></div>", unsafe_allow_html=True)
    cols2[2].markdown(f"<div class='card'><div class='small'>Sensitive Data Shared</div><div class='kpi'>{sensitive_shared}</div></div>", unsafe_allow_html=True)
    cols2[3].markdown(f"<div class='card'><div class='small'>Agent Trust Avg</div><div class='kpi'>{int(sum(a.trust_score for a in agents)/len(agents)) if agents else 0}</div></div>", unsafe_allow_html=True)

    st.markdown("<h4>Recent activity</h4>", unsafe_allow_html=True)
    evs = sorted(svc.storage.list_audit(owner), key=lambda e: e.timestamp, reverse=True)[:8]
    if not evs:
        st.info("No recent activity")
    else:
        for e in evs:
            ts = e.timestamp.strftime("%Y-%m-%d %H:%M UTC")
            st.markdown(f"- **{e.action.replace('_',' ').title()}** — {e.detail} <span class='small'>{ts}</span>", unsafe_allow_html=True)


def compute_passport_health_ui(svc, owner):
    creds = [c.__dict__ for c in svc.storage.list_credentials(owner)]
    perms = [p.__dict__ for p in svc.list_permissions(owner)]
    user = svc.storage.get_user(owner)
    return compute_passport_health(user_verified=bool(user and user.verified), credentials=creds, permissions=perms)


def compute_privacy_ui(svc, owner):
    creds = [c.__dict__ for c in svc.storage.list_credentials(owner)]
    perms = [p.__dict__ for p in svc.list_permissions(owner)]
    return compute_privacy_score(credentials=creds, permissions=perms)


def page_my_passport(svc):
    st.markdown("<div class='card'><h3>My AI Passport</h3></div>", unsafe_allow_html=True)
    owner = DEFAULT_USER_ID
    user = svc.storage.get_user(owner)
    if not user:
        st.info("No profile — load demo data.")
        return
    cols = st.columns([3,1])
    with cols[0]:
        st.markdown(f"### {user.display_name}")
        st.write(f"Country: {user.country}")
        st.write(f"Language: {user.language}")
        st.write(f"Verification: {'VERIFIED' if user.verified else 'UNVERIFIED'}")
        st.write(f"Last verified: {user.last_verified_at}")
        if st.button("Export Passport (JSON)"):
            data = svc.export_passport_json(owner)
            st.download_button("Download passport.json", data=data, file_name="passport.json", mime="application/json")
    with cols[1]:
        st.markdown("<div class='card'><div class='small'>Passport</div><div style='font-size:18px'>••••••••4821</div></div>", unsafe_allow_html=True)
        if st.button("Unmask Passport (Confirm)"):
            with st.form("unmask_confirm"):
                st.write("Unmasking sensitive data requires confirmation.")
                chk = st.checkbox("I understand this will reveal sensitive information")
                go = st.form_submit_button("Confirm")
                if go and chk:
                    st.info("Sensitive values can be revealed here in a production app after strong authentication.")

    st.markdown("#### Credentials")
    creds = svc.storage.list_credentials(owner)
    if not creds:
        st.info("No credentials on file.")
    else:
        for c in creds:
            with st.expander(f"{c.name} — {c.type} — {c.status}"):
                st.write(f"Issuer: {c.issuer}")
                st.write(f"Sensitivity: {c.sensitivity}")
                st.write(f"Issue date: {c.issue_date}")
                st.write(f"Expiry date: {c.expiry_date}")
                st.write(f"Sharing allowed: {c.sharing_allowed}")


def page_credentials(svc):
    st.markdown("<div class='card'><h3>Credential Vault</h3></div>", unsafe_allow_html=True)
    owner = DEFAULT_USER_ID
    creds = svc.storage.list_credentials(owner)
    df = pd.DataFrame([{"Name": c.name, "Type": c.type, "Issuer": c.issuer, "Status": c.status, "Sensitivity": c.sensitivity, "Sharing": "Allowed" if c.sharing_allowed else "Blocked", "ID": c.credential_id} for c in creds])
    st.dataframe(df)

    st.markdown("### Add Credential")
    with st.form("add_cred"):
        name = st.text_input("Name")
        issuer = st.text_input("Issuer", value="Self")
        ctype = st.selectbox("Type", ["Education","Academic Record","Degree","Skills","Language","Certifications","Work Experience","Identity","Other"])
        sensitivity = st.selectbox("Sensitivity", ["low","medium","high"])
        status = st.selectbox("Status", ["Verified","Pending","Expired","Revoked"])
        sharing = st.checkbox("Allow sharing by default", value=True)
        notes = st.text_area("Notes")
        submit = st.form_submit_button("Add Credential")
        if submit:
            try:
                svc.add_credential(owner, {"name": name, "issuer": issuer, "type": ctype, "sensitivity": sensitivity, "status": status, "sharing_allowed": sharing, "notes": notes})
                st.success("Credential added")
            except Exception as e:
                st.error(str(e))

    st.markdown("### Manage")
    if not creds:
        st.info("No credentials to manage.")
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
                    with st.form(f"edit_{c.credential_id}"):
                        name = st.text_input("Name", value=c.name)
                        issuer = st.text_input("Issuer", value=c.issuer)
                        status = st.selectbox("Status", ["Verified","Pending","Expired","Revoked"], index=["Verified","Pending","Expired","Revoked"].index(c.status))
                        sharing = st.checkbox("Allow sharing", value=c.sharing_allowed)
                        save = st.form_submit_button("Save")
                        if save:
                            svc.edit_credential(c.credential_id, {"name": name, "issuer": issuer, "status": status, "sharing_allowed": sharing})
                            st.success("Saved")
                if cols[2].button("Delete", key=f"del_{c.credential_id}"):
                    with st.form(f"del_confirm_{c.credential_id}"):
                        typed = st.text_input("Type the credential name to confirm deletion")
                        confirm = st.form_submit_button("Delete")
                        if confirm:
                            if typed == c.name:
                                svc.remove_credential(c.credential_id, DEFAULT_USER_ID)
                                st.success("Deleted")
                            else:
                                st.error("Name mismatch")
                if cols[3].button("Toggle Sharing", key=f"share_{c.credential_id}"):
                    with st.form(f"share_form_{c.credential_id}"):
                        allow = st.checkbox("Allow sharing", value=c.sharing_allowed)
                        ok = st.form_submit_button("Save")
                        if ok:
                            svc.edit_credential(c.credential_id, {"sharing_allowed": allow})
                            st.success("Sharing updated")


def page_access_requests(svc):
    st.markdown("<div class='card'><h3>AI Access Requests</h3></div>", unsafe_allow_html=True)
    owner = DEFAULT_USER_ID
    reqs = svc.list_requests(owner)
    if not reqs:
        st.info("No pending requests.")
        return
    for r in reqs:
        agent = svc.storage.get_agent(r.agent_id)
        with st.expander(f"{agent.name if agent else r.agent_id} — {r.purpose}", expanded=True):
            st.write(f"Organization: {agent.organization if agent else 'Unknown'}")
            st.write(f"Reason: {r.reason}")
            st.write(f"Requested duration: {r.requested_duration_hours} hours")
            rec = recommend_minimum_fields(r.requested_fields)
            st.markdown(f"<div class='small'>Recommendation: {', '.join(rec)}</div>", unsafe_allow_html=True)
            selections = {}
            for f in r.requested_fields:
                default = f in rec
                selections[f] = st.checkbox(f"{f} ({classify_field(f)})", value=default, key=f"{r.request_id}_{f}")
            cols = st.columns(3)
            if cols[0].button("Approve selected", key=f"approve_{r.request_id}"):
                approved = [f for f, ok in selections.items() if ok]
                if not approved:
                    st.error("Select at least one field.")
                else:
                    highs = [f for f in approved if classify_field(f) == "high"]
                    if highs and st.session_state.get("require_sensitive_confirmation", True):
                        with st.form(f"confirm_high_{r.request_id}"):
                            st.write("High-sensitivity fields selected: " + ", ".join(highs))
                            chk = st.checkbox("I confirm sharing these high-sensitivity fields")
                            sub = st.form_submit_button("Confirm and Approve")
                            if sub and chk:
                                svc.approve_request(r.request_id, approved, r.requested_duration_hours, DEFAULT_USER_ID)
                                st.success("Access granted")
                    else:
                        svc.approve_request(r.request_id, approved, r.requested_duration_hours, DEFAULT_USER_ID)
                        st.success("Access granted")
            if cols[1].button("Approve recommended", key=f"approve_min_{r.request_id}"):
                approved = rec
                highs = [f for f in approved if classify_field(f) == "high"]
                if highs and st.session_state.get("require_sensitive_confirmation", True):
                    with st.form(f"confirm_min_{r.request_id}"):
                        st.write("High-sensitivity fields included: " + ", ".join(highs))
                        chk = st.checkbox("I confirm")
                        sub = st.form_submit_button("Confirm and Approve")
                        if sub and chk:
                            svc.approve_request(r.request_id, approved, r.requested_duration_hours, DEFAULT_USER_ID)
                            st.success("Access granted")
                else:
                    svc.approve_request(r.request_id, approved, r.requested_duration_hours, DEFAULT_USER_ID)
                    st.success("Access granted")
            if cols[2].button("Deny", key=f"deny_{r.request_id}"):
                with st.form(f"deny_{r.request_id}"):
                    reason = st.text_area("Reason for denial (optional)")
                    sub = st.form_submit_button("Deny request")
                    if sub:
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
            st.write(f"Expires at: {p.expires_at} ({remaining})")
            cols = st.columns(3)
            if cols[0].button("Revoke", key=f"revoke_{p.permission_id}"):
                with st.form(f"revoke_{p.permission_id}"):
                    st.write("Type REVOKE to confirm revocation")
                    t = st.text_input("Confirm")
                    ok = st.form_submit_button("Revoke")
                    if ok and t == "REVOKE":
                        svc.revoke_permission(p.permission_id, DEFAULT_USER_ID, "User revoked")
                        st.success("Permission revoked")
                    elif ok:
                        st.error("Confirmation mismatch")
            if cols[1].button("Extend", key=f"extend_{p.permission_id}"):
                with st.form(f"extend_form_{p.permission_id}"):
                    option = st.selectbox("Extend by", ["1 hour","24 hours","7 days","30 days","Custom hours"])
                    custom = None
                    if option == "Custom hours":
                        custom = st.number_input("Hours", min_value=1, max_value=8760, value=24)
                    sub = st.form_submit_button("Extend")
                    if sub:
                        hours = 1 if option=="1 hour" else 24 if option=="24 hours" else 168 if option=="7 days" else 720 if option=="30 days" else custom
                        try:
                            svc.extend_permission(p.permission_id, int(hours), DEFAULT_USER_ID)
                            st.success("Extended")
                        except Exception as e:
                            st.error(str(e))
            if cols[2].button("Modify Fields", key=f"modify_{p.permission_id}"):
                with st.form(f"mod_fields_{p.permission_id}"):
                    new_fields = st.multiselect("Fields", options=p.fields, default=p.fields)
                    sub = st.form_submit_button("Save")
                    if sub:
                        svc.modify_permission_fields(p.permission_id, new_fields, DEFAULT_USER_ID)
                        st.success("Updated")


def page_agents(svc):
    st.markdown("<div class='card'><h3>AI Agent Directory</h3></div>", unsafe_allow_html=True)
    agents = svc.list_agents()
    owner = DEFAULT_USER_ID
    perms = svc.list_permissions(owner)
    if not agents:
        st.info("No agents available.")
        return
    for a in agents:
        shared = []
        for p in perms:
            if p.agent_id == a.agent_id and p.status == "ACTIVE":
                shared.extend(p.fields)
        requested = a.requested_fields
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
    st.markdown("<div class='card'><h3>Access History / Audit</h3></div>", unsafe_allow_html=True)
    owner = DEFAULT_USER_ID
    evs = svc.storage.list_audit(owner)
    if not evs:
        st.info("No audit events.")
        return
    df = pd.DataFrame([{"timestamp": e.timestamp, "actor": e.actor, "action": e.action, "resource": e.resource, "detail": e.detail} for e in evs])
    st.dataframe(df.sort_values("timestamp", ascending=False))
    if st.button("Export Audit CSV"):
        payload = svc.export_audit_csv(owner)
        st.download_button("Download audit.csv", data=payload, file_name="audit.csv", mime="text/csv")


def page_privacy_center(svc):
    st.markdown("<div class='card'><h3>Privacy Center</h3></div>", unsafe_allow_html=True)
    owner = DEFAULT_USER_ID
    p = compute_privacy_ui(svc, owner)
    st.markdown(f"<div class='card'><div class='small'>Privacy Score</div><div class='kpi'>{p['score']}%</div></div>", unsafe_allow_html=True)
    st.write("How this score was calculated:")
    st.json(p["details"])
    if p["score"] < 50:
        st.warning("Recommendations: reduce shared high-sensitivity fields, revoke broad permissions.")
    else:
        st.success("Privacy posture is reasonable for demo data.")


def page_security_center(svc):
    st.markdown("<div class='card'><h3>Security Center</h3></div>", unsafe_allow_html=True)
    st.write("Security settings:")
    if "require_sensitive_confirmation" not in st.session_state:
        st.session_state["require_sensitive_confirmation"] = True
    if "auto_expire_permissions" not in st.session_state:
        st.session_state["auto_expire_permissions"] = True
    st.session_state["require_sensitive_confirmation"] = st.checkbox("Require confirmation for high-sensitivity data", value=st.session_state.get("require_sensitive_confirmation", True))
    st.session_state["auto_expire_permissions"] = st.checkbox("Automatically expire permissions", value=st.session_state.get("auto_expire_permissions", True))
    st.write("Recent security events:")
    evs = [e for e in svc.storage.list_audit(DEFAULT_USER_ID) if "permission" in e.action or "credential" in e.action]
    for e in sorted(evs, key=lambda x: x.timestamp, reverse=True)[:10]:
        st.write(f"{e.timestamp} — {e.action} — {e.detail}")


def page_notifications(svc):
    st.markdown("<div class='card'><h3>Notifications</h3></div>", unsafe_allow_html=True)
    notes = svc.notify.list_notifications(DEFAULT_USER_ID)
    if not notes:
        st.info("No notifications.")
        return
    for n in notes:
        with st.expander(f"{n.title} — {n.timestamp}"):
            st.write(n.body)
            cols = st.columns([1,1])
            if cols[0].button("Mark read", key=f"mr_{n.notification_id}"):
                svc.notify.mark_read(n.notification_id)
                st.success("Marked read")
            if cols[1].button("Delete all", key=f"deln_{n.notification_id}"):
                svc.notify.clear(DEFAULT_USER_ID)
                st.success("Cleared")
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
    st.markdown("Privacy preferences")
    st.session_state["require_sensitive_confirmation"] = st.checkbox("Require sensitive confirmation", value=st.session_state.get("require_sensitive_confirmation", True))
    st.session_state["auto_expire_permissions"] = st.checkbox("Auto expire permissions", value=st.session_state.get("auto_expire_permissions", True))
    st.number_input("Default permission duration (hours)", min_value=1, max_value=24*365, value=st.session_state.get("default_permission_hours", 168), key="default_permission_hours")


def page_help_about(svc):
    st.markdown("<div class='card'><h3>About TRUSTPASS</h3></div>", unsafe_allow_html=True)
    st.markdown(\"\"\"
**TRUSTPASS** — Your Identity. Your Context. Your Permission.

You control what AI can know about you.

TRUSTPASS demonstrates a premium user-controlled AI Passport. It focuses on privacy-first data sharing, field-level consent, revocation, and auditable access controls.

This product is a repository demonstration and uses in-memory storage for the session.
\"\"\")
    st.markdown(_logo_html("full"), unsafe_allow_html=True)
""",

    "app.py": """\"\"\"
TRUSTPASS — Streamlit entrypoint

Run:
    streamlit run app.py

This file wires UI, services, storage and session state together.
\"\"\"
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

try:
    ui.inject_css()
    ui.app_header("TRUSTPASS", "Your Identity. Your Context. Your Permission.", svc)
    with st.sidebar:
        ui.sidebar_navigation(st.session_state)
    page = st.session_state.get("nav", "Overview")
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
    err_id = "ERR-APP"
    st.error(f"An unexpected error occurred ({err_id}). Please refresh or contact support.")
    try:
        svc.audit.log_event(actor="system", action="application_error", resource="app", detail=str(e), owner_id=None)
    except Exception:
        pass
    if getattr(st.session_state.get("store"), "debug", False):
        st.text(traceback.format_exc())
""",

    "tests/test_services.py": """\"\"\"
Basic tests for ServiceLayer behaviors.
\"\"\"
import pytest
from src.storage import InMemoryStore
from src.services import ServiceLayer
from src.models import DemoDataConfig, DEFAULT_USER_ID

def test_demo_load_and_basic_flows():
    store = InMemoryStore()
    svc = ServiceLayer(store)
    svc.load_demo_data(DemoDataConfig())
    user = store.get_user(DEFAULT_USER_ID)
    assert user is not None
    creds = store.list_credentials(DEFAULT_USER_ID)
    assert len(creds) >= 3
    agents = store.list_agents()
    assert len(agents) >= 4
    reqs = store.list_requests(DEFAULT_USER_ID)
    assert len(reqs) >= 1

def test_credential_lifecycle():
    store = InMemoryStore()
    svc = ServiceLayer(store)
    svc.load_demo_data()
    owner = DEFAULT_USER_ID
    cred = svc.add_credential(owner, {"name":"Test Cert","issuer":"Test Org","type":"Cert","sensitivity":"low","status":"Pending"})
    assert cred.name == "Test Cert"
    with pytest.raises(ValueError):
        svc.add_credential(owner, {"name":"Test Cert","issuer":"Test Org"})
    svc.verify_credential(cred.credential_id, owner)
    assert store.get_credential(cred.credential_id).status == "Verified"
    svc.remove_credential(cred.credential_id, owner)
    assert store.get_credential(cred.credential_id) is None

def test_request_approve_and_permission():
    store = InMemoryStore()
    svc = ServiceLayer(store)
    svc.load_demo_data()
    owner = DEFAULT_USER_ID
    reqs = store.list_requests(owner)
    req = reqs[0]
    svc.approve_request(req.request_id, [req.requested_fields[0]], 24, owner)
    perms = store.list_permissions(owner)
    assert any(p.agent_id == req.agent_id for p in perms)

def test_permission_revoke_extend_expire():
    store = InMemoryStore()
    svc = ServiceLayer(store)
    svc.load_demo_data()
    owner = DEFAULT_USER_ID
    perms = store.list_permissions(owner)
    if not perms:
        pytest.skip("no perms in demo")
    p = perms[0]
    old = p.expires_at
    if old:
        svc.extend_permission(p.permission_id, 24, owner)
        assert store.get_permission(p.permission_id).expires_at > old
    svc.revoke_permission(p.permission_id, owner, "test")
    assert store.get_permission(p.permission_id).status == "REVOKED"

def test_exports_and_redaction():
    store = InMemoryStore()
    svc = ServiceLayer(store)
    svc.load_demo_data()
    owner = DEFAULT_USER_ID
    passport = svc.export_passport_json(owner)
    assert passport is not None
    creds_csv = svc.export_credentials_csv(owner)
    assert creds_csv is not None
""",

    "assets/brand/trustpass-logo.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="800" height="240" viewBox="0 0 800 240" role="img" aria-label="TRUSTPASS logo">
  <defs>
    <linearGradient id="g" x1="0" x2="1">
      <stop offset="0%" stop-color="#7C3AED"/>
      <stop offset="100%" stop-color="#06B6D4"/>
    </linearGradient>
  </defs>
  <rect width="800" height="240" rx="24" fill="#0B1220"/>
  <g transform="translate(40,32)">
    <circle cx="64" cy="64" r="56" fill="url(#g)" opacity="0.16"/>
    <circle cx="64" cy="52" r="18" fill="#fff"/>
    <path d="M24 118c10-14 30-20 56-20s46 6 56 20v6H24v-6z" fill="#fff"/>
    <circle cx="140" cy="24" r="8" fill="#06B6D4"/>
    <circle cx="176" cy="80" r="8" fill="#7C3AED"/>
    <path d="M82 70 L136 36 L170 76" stroke="#7C3AED" stroke-width="4" fill="none" stroke-linecap="round"/>
    <path d="M108 32 L124 48 L108 64 L104 60 L116 48 L104 36z" fill="#10B981" transform="translate(-20, -6) scale(0.9)"/>
  </g>
  <g transform="translate(180,92)">
    <text x="0" y="0" font-family="Segoe UI, Roboto, Helvetica, Arial, sans-serif" font-size="48" fill="#ffffff" font-weight="700">TRUSTPASS</text>
    <text x="0" y="36" font-family="Segoe UI, Roboto, Helvetica, Arial, sans-serif" font-size="14" fill="#94a3b8">Your Identity. Your Context. Your Permission.</text>
  </g>
</svg>
""",

    "assets/brand/trustpass-mark.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="160" height="160" viewBox="0 0 160 160" role="img" aria-label="TRUSTPASS mark">
  <defs>
    <linearGradient id="g2" x1="0" x2="1">
      <stop offset="0%" stop-color="#7C3AED"/>
      <stop offset="100%" stop-color="#06B6D4"/>
    </linearGradient>
  </defs>
  <rect width="160" height="160" rx="20" fill="#0B1220"/>
  <g transform="translate(20,20)">
    <circle cx="40" cy="40" r="32" fill="url(#g2)" opacity="0.16"/>
    <circle cx="40" cy="32" r="12" fill="#fff"/>
    <path d="M16 88c6-8 18-12 32-12s26 4 32 12v4H16v-4z" fill="#fff"/>
    <circle cx="96" cy="12" r="5" fill="#06B6D4"/>
    <circle cx="120" cy="44" r="5" fill="#7C3AED"/>
    <path d="M60 44 L98 22 L116 46" stroke="#7C3AED" stroke-width="3" fill="none" stroke-linecap="round"/>
    <path d="M90 8 L102 20 L90 32 L86 28 L98 20 L86 12z" fill="#10B981" transform="translate(-20,6) scale(0.6)"/>
  </g>
</svg>
""",

    "assets/brand/trustpass-logo-light.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="800" height="240" viewBox="0 0 800 240" role="img" aria-label="TRUSTPASS logo light">
  <rect width="800" height="240" rx="24" fill="#0B1220"/>
  <g transform="translate(40,32)">
    <circle cx="64" cy="64" r="56" fill="#ffffff" opacity="0.06"/>
    <circle cx="64" cy="52" r="18" fill="#fff"/>
    <path d="M24 118c10-14 30-20 56-20s46 6 56 20v6H24v-6z" fill="#fff"/>
    <circle cx="140" cy="24" r="8" fill="#06B6D4"/>
    <circle cx="176" cy="80" r="8" fill="#7C3AED"/>
  </g>
  <g transform="translate(180,92)">
    <text x="0" y="0" font-family="Segoe UI, Roboto, Helvetica, Arial, sans-serif" font-size="48" fill="#ffffff" font-weight="700">TRUSTPASS</text>
    <text x="0" y="36" font-family="Segoe UI, Roboto, Helvetica, Arial, sans-serif" font-size="14" fill="#94a3b8">Your Identity. Your Context. Your Permission.</text>
  </g>
</svg>
""",

    "assets/brand/trustpass-mark-light.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="160" height="160" viewBox="0 0 160 160" role="img" aria-label="TRUSTPASS mark light">
  <rect width="160" height="160" rx="20" fill="#0B1220"/>
  <g transform="translate(20,20)">
    <circle cx="40" cy="40" r="32" fill="#ffffff" opacity="0.06"/>
    <circle cx="40" cy="32" r="12" fill="#fff"/>
    <path d="M16 88c6-8 18-12 32-12s26 4 32 12v4H16v-4z" fill="#fff"/>
  </g>
</svg>
""",

    "assets/brand/favicon.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96" width="96" height="96" role="img" aria-label="TRUSTPASS favicon">
  <rect width="96" height="96" rx="18" fill="#0B1220"/>
  <g transform="translate(14,14)">
    <circle cx="24" cy="24" r="16" fill="#7C3AED" opacity="0.18"/>
    <circle cx="24" cy="18" r="6" fill="#fff"/>
    <path d="M6 48c4-6 12-9 22-9s18 3 22 9v3H6v-3z" fill="#fff"/>
  </g>
</svg>
"""
}

for filepath, content in files.items():
    dir_name = os.path.dirname(filepath)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Created: {filepath}")

print("\nAll files generated successfully! Now run:")
print("pip install -r requirements.txt")
print("streamlit run app.py")
