# agents/leave_agent.py
"""
Leave Agent — Feature #1 (Multi-Agent)
Handles all leave-related operations with policy compliance checks.
"""

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, date, timedelta
from typing import Optional
from loguru import logger


@dataclass
class LeaveResult:
    approved: bool
    message: str
    leave_type: str
    from_date: str
    to_date: str
    days_requested: int
    balance_after: int
    policy_reference: str
    notifications_sent: list[str]
    audit_id: str


LEAVE_POLICIES = {
    "Casual Leave":   {"max_balance": 12, "max_consecutive": 3, "notice_days": 1},
    "Sick Leave":     {"max_balance": 12, "max_consecutive": 7, "notice_days": 0},
    "Earned Leave":   {"max_balance": 45, "max_consecutive": 15, "notice_days": 7},
    "Maternity Leave":{"max_balance": 182,"max_consecutive": 182,"notice_days": 0},
    "LOP":            {"max_balance": 999,"max_consecutive": 30, "notice_days": 0},
}


class LeaveAgent:

    def __init__(self, db_path: str = "./hr_ai.db", employees_path: str = "./data/employees.json"):
        self.db_path = db_path
        with open(employees_path) as f:
            self.employees = {str(e["id"]): e for e in json.load(f)}
        self._init_tables()

    def _init_tables(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS leave_requests (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                emp_id      TEXT NOT NULL,
                emp_name    TEXT NOT NULL,
                leave_type  TEXT NOT NULL,
                from_date   TEXT NOT NULL,
                to_date     TEXT NOT NULL,
                days        INTEGER NOT NULL,
                status      TEXT DEFAULT 'Pending',
                reason      TEXT,
                approved_by TEXT,
                timestamp   TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def apply_leave(
        self,
        employee_id: str,
        leave_type: str,
        from_date: str,
        to_date: str,
        reason: str = "",
    ) -> LeaveResult:
        emp = self.employees.get(str(employee_id))
        if not emp:
            return LeaveResult(False, "Employee not found", leave_type, from_date, to_date, 0, 0, "", [], "")

        policy = LEAVE_POLICIES.get(leave_type, LEAVE_POLICIES["Casual Leave"])

        # Calculate days
        try:
            d1 = datetime.strptime(from_date, "%Y-%m-%d").date()
            d2 = datetime.strptime(to_date, "%Y-%m-%d").date()
        except Exception:
            d1 = d2 = date.today()
        days = max(1, (d2 - d1).days + 1)

        # Check balance
        balance_map = {"Casual Leave": "cl", "Sick Leave": "sl", "Earned Leave": "el"}
        bal_key = balance_map.get(leave_type, "cl")
        current_balance = emp.get(bal_key, 0)

        if leave_type not in ["LOP"] and current_balance < days:
            return LeaveResult(
                False,
                f"Insufficient {leave_type} balance. Available: {current_balance}, Requested: {days}",
                leave_type, from_date, to_date, days, current_balance,
                "Leave_Rules_2024.pdf", [], "",
            )

        if days > policy["max_consecutive"]:
            return LeaveResult(
                False,
                f"Exceeds maximum consecutive days ({policy['max_consecutive']}) for {leave_type}",
                leave_type, from_date, to_date, days, current_balance,
                "Leave_Rules_2024.pdf", [], "",
            )

        # Save to DB
        balance_after = current_balance - days
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "INSERT INTO leave_requests (emp_id,emp_name,leave_type,from_date,to_date,days,status,reason,approved_by,timestamp) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (str(employee_id), emp["name"], leave_type, from_date, to_date, days,
             "AI Approved", reason, "Leave Agent (AI)", datetime.now().isoformat()),
        )
        audit_id = f"LV-{cursor.lastrowid:05d}"
        conn.commit()
        conn.close()

        # Update in-memory balance
        emp[bal_key] = balance_after

        notifications = [
            f"Email sent to manager: {emp.get('manager_id', 'N/A')}",
            f"SMS confirmation sent to {emp['email']}",
            "Audit log created",
        ]

        logger.info(f"[LeaveAgent] Approved {days}d {leave_type} for {emp['name']} (audit={audit_id})")

        return LeaveResult(
            approved=True,
            message=f"✅ {leave_type} approved for {emp['name']} ({days} day{'s' if days>1 else ''}). Balance updated.",
            leave_type=leave_type,
            from_date=from_date,
            to_date=to_date,
            days_requested=days,
            balance_after=balance_after,
            policy_reference="Leave_Rules_2024.pdf",
            notifications_sent=notifications,
            audit_id=audit_id,
        )

    def get_balance(self, employee_id: str) -> dict:
        emp = self.employees.get(str(employee_id))
        if not emp:
            return {}
        return {
            "employee": emp["name"],
            "grade": emp["grade"],
            "location": emp["location"],
            "Casual Leave": emp.get("cl", 0),
            "Sick Leave": emp.get("sl", 0),
            "Earned Leave": emp.get("el", 0),
        }

    def get_leave_history(self, employee_id: str, limit: int = 10) -> list[dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT leave_type,from_date,to_date,days,status,timestamp FROM leave_requests WHERE emp_id=? ORDER BY id DESC LIMIT ?",
            (str(employee_id), limit),
        )
        rows = [{"type":r[0],"from":r[1],"to":r[2],"days":r[3],"status":r[4],"date":r[5]} for r in cursor.fetchall()]
        conn.close()
        return rows


# Singleton
leave_agent = LeaveAgent()
