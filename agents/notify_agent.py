# agents/notify_agent.py
"""
Notification Agent — Feature #1 (Multi-Agent)
Simulates multi-channel notifications (email, SMS, in-app).
In production: replace with SendGrid (email), Twilio (SMS), Firebase (push).
"""

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from loguru import logger


@dataclass
class NotificationResult:
    sent: bool
    channels: list[str]
    recipients: list[str]
    message_id: str
    timestamp: str


class NotifyAgent:

    TEMPLATES = {
        "leave_approved":     "Hi {name}, your {leave_type} from {from_date} to {to_date} has been approved. Balance remaining: {balance} days.",
        "leave_rejected":     "Hi {name}, your {leave_type} request was rejected. Reason: {reason}. Contact HR for assistance.",
        "attrition_alert":    "Manager Alert: {emp_name} has been flagged as high attrition risk ({risk}%). Schedule a retention conversation.",
        "burnout_alert":      "HR Alert: {emp_name} (burnout score {score}%) requires immediate wellness intervention.",
        "compliance_violation":"HR Admin: Compliance violation detected for {emp_name} — {violation}. Action required: {action}.",
        "onboarding_started": "Welcome {name}! Your onboarding has started. Joining date: {date}. Your buddy: {buddy}.",
        "interview_scheduled":"Hi {candidate}, your interview for {role} is scheduled on {date} at {time}. Panel: {panel}.",
        "reimbursement_approved": "Hi {name}, reimbursement of ₹{amount} for {category} has been approved.",
    }

    def __init__(self, db_path: str = "./hr_ai.db"):
        self.db_path = db_path
        self._init_tables()

    def _init_tables(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                template    TEXT,
                recipients  TEXT,
                channels    TEXT,
                message     TEXT,
                status      TEXT DEFAULT 'sent',
                timestamp   TEXT
            )
        """)
        conn.commit()
        conn.close()

    def send(
        self,
        template: str,
        recipients: list[str],
        channels: list[str] = None,
        **kwargs,
    ) -> NotificationResult:
        if channels is None:
            channels = ["email", "in_app"]

        tmpl = self.TEMPLATES.get(template, "Notification: {message}")
        try:
            message = tmpl.format(**kwargs)
        except KeyError:
            message = str(kwargs)

        # Simulate sending (in production: call SendGrid / Twilio / Firebase)
        for channel in channels:
            for recipient in recipients:
                logger.info(f"[NotifyAgent] [{channel.upper()}] → {recipient}: {message[:80]}...")

        # Log to DB
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "INSERT INTO notifications (template,recipients,channels,message,timestamp) VALUES (?,?,?,?,?)",
            (template, ",".join(recipients), ",".join(channels), message, datetime.now().isoformat()),
        )
        msg_id = f"MSG-{cursor.lastrowid:06d}"
        conn.commit()
        conn.close()

        return NotificationResult(
            sent=True,
            channels=channels,
            recipients=recipients,
            message_id=msg_id,
            timestamp=datetime.now().isoformat(),
        )

    def send_leave_notification(self, emp_name: str, leave_type: str, from_date: str, to_date: str, balance: int, manager_email: str, emp_email: str):
        self.send("leave_approved", recipients=[emp_email, manager_email], channels=["email","sms","in_app"],
                  name=emp_name, leave_type=leave_type, from_date=from_date, to_date=to_date, balance=balance)

    def send_attrition_alert(self, emp_name: str, risk_pct: int, manager_email: str):
        self.send("attrition_alert", recipients=[manager_email, "hr@company.com"], channels=["email","in_app"],
                  emp_name=emp_name, risk=f"{risk_pct}%")

    def send_burnout_alert(self, emp_name: str, score: int, hrbp_email: str):
        self.send("burnout_alert", recipients=[hrbp_email, "wellness@company.com"], channels=["email","in_app"],
                  emp_name=emp_name, score=score)


# Singleton
notify_agent = NotifyAgent()
