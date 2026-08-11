# TRUSTPASS

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

IMPORTANT
- This is a hackathon product demonstration intended for local review and Streamlit Community Cloud deployment.
- Sensitive values are masked/redacted in UI, logs, and exports.
- No external APIs or credentials are required.

Installation
1. Create Python 3.8+ environment
2. Install dependencies:
   pip install -r requirements.txt
3. Run:
   streamlit run app.py

Limitations & Next Steps
- Single-user demo (no authentication)
- In-memory persistence (replace InMemoryStore for production)
- No cryptographic signed credentials — intended as a clear architecture and UX demonstration

Brand assets are in assets/brand/.

Tests are provided in tests/ but are marked as NOT EXECUTED in this bundle (execution environment not available here).
