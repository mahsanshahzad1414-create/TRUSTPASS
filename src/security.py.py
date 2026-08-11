"""
Security configuration and helpers (demo-level).
"""
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
