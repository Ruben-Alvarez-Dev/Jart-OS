"""
Jart-OS RBACManager — Role-Based Access Control
Spec: Fase 5 Punto 5 — Seguridad
"""

import logging
from typing import List

log = logging.getLogger("jart-os.core.rbac")


class RBACManager:
    """
    Role-Based Access Control for Jart-OS agents.

    Roles and permissions:
    - admin:     * (all)
    - director:  task:create, task:assign, task:monitor, task:cancel
    - executor:  task:execute, task:report
    - guardian:  task:validate, task:block
    - council:   task:review, task:approve
    - pipeline:  content:process, content:extract, content:chunk
    - user:      task:read, content:read
    """

    PERMISSIONS = {
        "admin": ["*"],
        "director": ["task:create", "task:assign", "task:monitor", "task:cancel", "task:read"],
        "executor": ["task:execute", "task:report", "task:read"],
        "guardian": ["task:validate", "task:block", "task:read"],
        "council": ["task:review", "task:approve", "task:read"],
        "pipeline": ["content:process", "content:extract", "content:chunk", "content:read"],
        "user": ["task:read", "content:read"],
        "session_manager": ["session:create", "session:cancel", "session:monitor"],
    }

    def has_permission(self, role: str, permission: str) -> bool:
        """Check if role has a specific permission."""
        allowed = self.PERMISSIONS.get(role, [])
        return "*" in allowed or permission in allowed

    def check_permission(self, role: str, permission: str) -> bool:
        """Check permission, raise PermissionError if denied."""
        if not self.has_permission(role, permission):
            log.warning(f"Permission denied: role={role} permission={permission}")
            return False
        return True

    def get_permissions(self, role: str) -> List[str]:
        """Get all permissions for a role."""
        return self.PERMISSIONS.get(role, [])

    def get_roles(self) -> List[str]:
        """Get all defined roles."""
        return list(self.PERMISSIONS.keys())

    def validate_role(self, role: str) -> bool:
        """Check if role exists."""
        return role in self.PERMISSIONS
