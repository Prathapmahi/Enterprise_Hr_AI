# utils/rbac.py
"""
Role-Based Access Control (RBAC) — AI Governance & Security Layer
Feature #13: Enterprise-grade AI safety
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional
from loguru import logger
import sqlite3
import json
from datetime import datetime


class Role(str, Enum):
    EMPLOYEE   = "employee"
    MANAGER    = "manager"
    HR_ADMIN   = "hr_admin"
    FINANCE    = "finance"
    IT_ADMIN   = "it_admin"
    CEO        = "ceo"


class Action(str, Enum):
    VIEW_OWN_PROFILE        = "view_own_profile"
    VIEW_OWN_SALARY         = "view_own_salary"
    VIEW_OWN_LEAVES         = "view_own_leaves"
    APPLY_LEAVE             = "apply_leave"
    VIEW_OTHERS_SALARY      = "view_others_salary"
    VIEW_TEAM_LEAVES        = "view_team_leaves"
    APPROVE_LEAVE           = "approve_leave"
    VIEW_ALL_SALARIES       = "view_all_salaries"
    RUN_PAYROLL             = "run_payroll"
    DELETE_EMPLOYEE         = "delete_employee"
    EXPORT_DATA             = "export_data"
    VIEW_ATTRITION_REPORT   = "view_attrition_report"
    MODIFY_POLICY           = "modify_policy"
    ACCESS_AUDIT_LOG        = "access_audit_log"


# ── Permission Matrix ─────────────────────────────────────────────────────────
PERMISSION_MATRIX: dict[Role, set[Action]] = {
    Role.EMPLOYEE: {
        Action.VIEW_OWN_PROFILE,
        Action.VIEW_OWN_SALARY,
        Action.VIEW_OWN_LEAVES,
        Action.APPLY_LEAVE,
    },
    Role.MANAGER: {
        Action.VIEW_OWN_PROFILE,
        Action.VIEW_OWN_SALARY,
        Action.VIEW_OWN_LEAVES,
        Action.APPLY_LEAVE,
        Action.VIEW_OTHERS_SALARY,
        Action.VIEW_TEAM_LEAVES,
        Action.APPROVE_LEAVE,
        Action.VIEW_ATTRITION_REPORT,
    },
    Role.HR_ADMIN: {
        Action.VIEW_OWN_PROFILE,
        Action.VIEW_OWN_SALARY,
        Action.VIEW_OWN_LEAVES,
        Action.APPLY_LEAVE,
        Action.VIEW_OTHERS_SALARY,
        Action.VIEW_TEAM_LEAVES,
        Action.APPROVE_LEAVE,
        Action.VIEW_ALL_SALARIES,
        Action.RUN_PAYROLL,
        Action.EXPORT_DATA,
        Action.VIEW_ATTRITION_REPORT,
        Action.ACCESS_AUDIT_LOG,
    },
    Role.FINANCE: {
        Action.VIEW_OWN_PROFILE,
        Action.VIEW_OWN_SALARY,
        Action.VIEW_OWN_LEAVES,
        Action.APPLY_LEAVE,
        Action.VIEW_ALL_SALARIES,
        Action.RUN_PAYROLL,
        Action.EXPORT_DATA,
        Action.ACCESS_AUDIT_LOG,
    },
    Role.IT_ADMIN: {
        Action.VIEW_OWN_PROFILE,
        Action.VIEW_OWN_SALARY,
        Action.VIEW_OWN_LEAVES,
        Action.APPLY_LEAVE,
        Action.ACCESS_AUDIT_LOG,
    },
    Role.CEO: {a for a in Action},  # Full access
}


@dataclass
class AccessResult:
    allowed: bool
    reason: str
    user_role: str
    action: str
    timestamp: str


class RBACEngine:
    """
    RBAC Engine — checks permissions and logs every access attempt.
    Every denied access creates an audit log entry.
    """

    def __init__(self, db_path: str = "./hr_ai.db"):
        self.db_path = db_path
        self._init_audit_table()

    def _init_audit_table(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rbac_audit_log (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id   TEXT NOT NULL,
                user_role TEXT NOT NULL,
                action    TEXT NOT NULL,
                allowed   INTEGER NOT NULL,
                reason    TEXT,
                ip_addr   TEXT,
                timestamp TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def check_permission(
        self,
        user_id: str,
        user_role: Role,
        action: Action,
        resource_owner_id: Optional[str] = None,
        ip_addr: str = "unknown",
    ) -> AccessResult:
        """
        Evaluate whether user_role can perform action.
        Logs every access attempt (allowed or denied).
        """
        allowed_actions = PERMISSION_MATRIX.get(user_role, set())
        allowed = action in allowed_actions

        # Special rule: employees can only view their own salary
        if action == Action.VIEW_OTHERS_SALARY and user_role == Role.EMPLOYEE:
            if resource_owner_id and resource_owner_id == user_id:
                allowed = True
                reason = "Viewing own salary — permitted"
            else:
                allowed = False
                reason = "Employees cannot view other employees' salary"
        elif allowed:
            reason = f"Role '{user_role.value}' has permission for '{action.value}'"
        else:
            reason = f"Role '{user_role.value}' does NOT have permission for '{action.value}'"

        result = AccessResult(
            allowed=allowed,
            reason=reason,
            user_role=user_role.value,
            action=action.value,
            timestamp=datetime.now().isoformat(),
        )

        self._log_audit(user_id, user_role.value, action.value, allowed, reason, ip_addr)

        if not allowed:
            logger.warning(
                f"[RBAC DENIED] user={user_id} role={user_role.value} "
                f"action={action.value} ip={ip_addr}"
            )
        else:
            logger.debug(
                f"[RBAC ALLOWED] user={user_id} role={user_role.value} action={action.value}"
            )

        return result

    def _log_audit(self, user_id, role, action, allowed, reason, ip_addr):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                "INSERT INTO rbac_audit_log (user_id,user_role,action,allowed,reason,ip_addr,timestamp) "
                "VALUES (?,?,?,?,?,?,?)",
                (user_id, role, action, int(allowed), reason, ip_addr, datetime.now().isoformat()),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Audit log write failed: {e}")

    def get_recent_audit_logs(self, limit: int = 20) -> list[dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT * FROM rbac_audit_log ORDER BY id DESC LIMIT ?", (limit,)
        )
        cols = [d[0] for d in cursor.description]
        rows = [dict(zip(cols, row)) for row in cursor.fetchall()]
        conn.close()
        return rows


# Singleton
rbac_engine = RBACEngine()
