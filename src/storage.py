"""
In-memory storage for TRUSTPASS. Designed to be replaceable by a database-backed implementation.
Provides owner-aware collections and helper operations for audit and notifications.
"""
from typing import Dict, List, Optional
from datetime import datetime, timezone
from .models import (
    User,
    Credential,
    AIAgent,
    Permission,
    AccessRequest,
    AuditEvent,
    Notification,
    new_id,
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

    # Demo helpers
    def has_demo_loaded(self) -> bool:
        return self._demo_loaded

    def set_demo_loaded(self, v: bool = True):
        self._demo_loaded = v

    def reset(self):
        # Clear all data while preserving configuration
        self.users.clear()
        self.credentials.clear()
        self.agents.clear()
        self.permissions.clear()
        self.requests.clear()
        self.audit.clear()
        self.notifications.clear()
        self._demo_loaded = False

    # Users
    def add_user(self, user: User):
        self.users[user.user_id] = user

    def get_user(self, user_id: str) -> Optional[User]:
        return self.users.get(user_id)

    # Credentials
    def add_credential(self, cred: Credential):
        self.credentials[cred.credential_id] = cred

    def list_credentials(self, owner_id: str) -> List[Credential]:
        return [c for c in self.credentials.values() if c.owner_id == owner_id]

    def get_credential(self, credential_id: str) -> Optional[Credential]:
        return self.credentials.get(credential_id)

    def remove_credential(self, credential_id: str):
        if credential_id in self.credentials:
            del self.credentials[credential_id]

    # Agents
    def add_agent(self, agent: AIAgent):
        self.agents[agent.agent_id] = agent

    def list_agents(self) -> List[AIAgent]:
        return list(self.agents.values())

    def get_agent(self, agent_id: str) -> Optional[AIAgent]:
        return self.agents.get(agent_id)

    # Permissions
    def add_permission(self, perm: Permission):
        self.permissions[perm.permission_id] = perm

    def list_permissions(self, owner_id: str) -> List[Permission]:
        return [p for p in self.permissions.values() if p.owner_id == owner_id]

    def get_permission(self, permission_id: str) -> Optional[Permission]:
        return self.permissions.get(permission_id)

    def update_permission(self, permission_id: str, perm: Permission):
        self.permissions[permission_id] = perm

    def remove_permission(self, permission_id: str):
        if permission_id in self.permissions:
            del self.permissions[permission_id]

    # Requests
    def add_request(self, req: AccessRequest):
        self.requests[req.request_id] = req

    def list_requests(self, owner_id: str) -> List[AccessRequest]:
        return [r for r in self.requests.values() if r.owner_id == owner_id and not r.handled]

    def get_request(self, request_id: str) -> Optional[AccessRequest]:
        return self.requests.get(request_id)

    def mark_request_handled(self, request_id: str):
        r = self.requests.get(request_id)
        if r:
            r.handled = True
            self.requests[request_id] = r

    # Audit
    def add_audit(self, event: AuditEvent):
        self.audit[event.event_id] = event

    def list_audit(self, owner_id: Optional[str] = None) -> List[AuditEvent]:
        if owner_id is None:
            return list(self.audit.values())
        return [e for e in self.audit.values() if e.owner_id == owner_id]

    # Notifications
    def add_notification(self, n: Notification):
        self.notifications[n.notification_id] = n

    def list_notifications(self, owner_id: Optional[str] = None) -> List[Notification]:
        if owner_id is None:
            return list(self.notifications.values())
        return [n for n in self.notifications.values() if n.owner_id == owner_id]

    def mark_notification_read(self, notification_id: str):
        n = self.notifications.get(notification_id)
        if n:
            n.unread = False
            self.notifications[notification_id] = n

    def mark_all_notifications_read(self, owner_id: str):
        for n in self.notifications.values():
            if n.owner_id == owner_id:
                n.unread = False

    def clear_notifications(self, owner_id: Optional[str] = None):
        if owner_id is None:
            self.notifications.clear()
        else:
            ids = [nid for nid, n in self.notifications.items() if n.owner_id == owner_id]
            for nid in ids:
                del self.notifications[nid]
