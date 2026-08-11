"""
Lightweight security configuration for TRUSTPASS (prototype-level controls).
Contains toggles that affect application behavior and helper functions.
"""
from datetime import timedelta

# Application-level security defaults (demo-level, not production secure)
SECURITY_DEFAULTS = {
    "require_sensitive_confirmation": True,
    "auto_expire_permissions": True,
    "session_timeout_minutes": 60,
}

# Acceptable durations for permissions (hours)
PERMISSION_DURATIONS = [1, 24, 168, 720]

# Sensitivity levels and colors for UI mapping
SENSITIVITY_COLORS = {
    "low": "#06b6d4",      # cyan
    "medium": "#f59e0b",   # amber
    "high": "#ef4444",     # red
}


def is_sensitive(field_sensitivity: str) -> bool:
    return (field_sensitivity or "").lower() == "high"
