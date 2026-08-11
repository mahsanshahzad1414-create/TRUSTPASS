"""
Data models for TRUSTPASS (dataclasses and helpers).
"""
from __future__ import annotations
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
    load_sample_agents: bool = True


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
        # hide sensitive fields from default public view
        if "passport_number_masked" in d:
            d["passport_number_masked"] = "••••••••0000"
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
    scope: str  # e.g., limited|broad
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
    handled: bool = False  # mark when approved/denied


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
