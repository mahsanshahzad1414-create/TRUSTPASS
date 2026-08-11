"""
Basic tests for ServiceLayer behaviors.
"""
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
