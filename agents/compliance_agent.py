# agents/compliance_agent.py
"""
AI Compliance Monitoring — Feature #16
Cross-System Enterprise AI — Feature #19
Monitors policy violations, attendance anomalies, and generates compliance reports.
"""

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from loguru import logger


@dataclass
class ComplianceViolation:
    employee_id: int
    employee_name: str
    violation_type: str
    severity: str        # HIGH / MEDIUM / LOW
    description: str
    policy_reference: str
    detected_at: str
    action_required: str


@dataclass
class ComplianceReport:
    generated_at: str
    total_violations: int
    critical_count: int
    medium_count: int
    low_count: int
    violations: list[ComplianceViolation]
    department_scores: dict
    recommendations: list[str]


COMPLIANCE_RULES = [
    {
        "id": "CR-001",
        "name": "Overtime Policy",
        "check": lambda emp: emp.get("overtime", 0) > 60,
        "severity": "HIGH",
        "description": lambda emp: f"Working {emp.get('overtime',0)}hrs/week (policy: max 60)",
        "policy": "HR_Policy_v4.2.pdf § Work Hours",
        "action": "Immediate manager + HR intervention. Workload redistribution required.",
    },
    {
        "id": "CR-002",
        "name": "Mandatory Leave",
        "check": lambda emp: (emp.get("cl",0) + emp.get("sl",0)) < 5,
        "severity": "MEDIUM",
        "description": lambda emp: f"Total leave balance {emp.get('cl',0)+emp.get('sl',0)} days — possible unreported mandatory leave",
        "policy": "Leave_Rules_2024.pdf § Mandatory Leave",
        "action": "HR to ensure mandatory leave compliance. Block calendar if needed.",
    },
    {
        "id": "CR-003",
        "name": "Burnout Threshold",
        "check": lambda emp: emp.get("burnout", 0) > 85,
        "severity": "HIGH",
        "description": lambda emp: f"Burnout score {emp.get('burnout',0)}% — exceeds critical threshold of 85%",
        "policy": "HR_Policy_v4.2.pdf § Employee Wellbeing",
        "action": "Refer to Employee Assistance Programme. HRBP counselling mandatory.",
    },
    {
        "id": "CR-004",
        "name": "High Attrition Risk",
        "check": lambda emp: emp.get("risk", 0) > 75,
        "severity": "HIGH",
        "description": lambda emp: f"Attrition risk {emp.get('risk',0)}% — retention intervention required",
        "policy": "HR_Policy_v4.2.pdf § Talent Retention",
        "action": "Schedule retention conversation. Escalate to L5+ manager and CHRO.",
    },
    {
        "id": "CR-005",
        "name": "Negative Sentiment",
        "check": lambda emp: emp.get("sentiment", 0) < -0.4,
        "severity": "MEDIUM",
        "description": lambda emp: f"Persistent negative sentiment score {emp.get('sentiment',0):.2f}",
        "policy": "HR_Policy_v4.2.pdf § Employee Engagement",
        "action": "Confidential 1:1 with HRBP. Anonymous feedback encouraged.",
    },
]


class ComplianceAgent:

    def __init__(self, employees_path: str = "./data/employees.json", db_path: str = "./hr_ai.db"):
        with open(employees_path) as f:
            self.employees = json.load(f)
        self.db_path = db_path
        self._init_tables()

    def _init_tables(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS compliance_violations (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                emp_id      INTEGER,
                emp_name    TEXT,
                rule_id     TEXT,
                severity    TEXT,
                description TEXT,
                policy_ref  TEXT,
                action      TEXT,
                resolved    INTEGER DEFAULT 0,
                timestamp   TEXT
            )
        """)
        conn.commit()
        conn.close()

    def run_compliance_check(self) -> ComplianceReport:
        """Run all compliance rules against all employees."""
        violations: list[ComplianceViolation] = []

        for emp in self.employees:
            for rule in COMPLIANCE_RULES:
                if rule["check"](emp):
                    v = ComplianceViolation(
                        employee_id=emp["id"],
                        employee_name=emp["name"],
                        violation_type=rule["name"],
                        severity=rule["severity"],
                        description=rule["description"](emp),
                        policy_reference=rule["policy"],
                        detected_at=datetime.now().isoformat(),
                        action_required=rule["action"],
                    )
                    violations.append(v)
                    self._save_violation(emp, rule, v)

        dept_scores = self._compute_dept_scores(violations)
        recs = self._generate_recommendations(violations)

        report = ComplianceReport(
            generated_at=datetime.now().isoformat(),
            total_violations=len(violations),
            critical_count=sum(1 for v in violations if v.severity == "HIGH"),
            medium_count=sum(1 for v in violations if v.severity == "MEDIUM"),
            low_count=sum(1 for v in violations if v.severity == "LOW"),
            violations=violations,
            department_scores=dept_scores,
            recommendations=recs,
        )

        logger.info(
            f"[ComplianceAgent] Scan complete — {report.total_violations} violations "
            f"({report.critical_count} critical, {report.medium_count} medium)"
        )
        return report

    def _save_violation(self, emp, rule, v):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                "INSERT INTO compliance_violations (emp_id,emp_name,rule_id,severity,description,policy_ref,action,timestamp) VALUES (?,?,?,?,?,?,?,?)",
                (emp["id"], emp["name"], rule["id"], v.severity, v.description, v.policy_reference, v.action_required, v.detected_at),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to save violation: {e}")

    def _compute_dept_scores(self, violations: list[ComplianceViolation]) -> dict:
        dept_violations: dict[str, int] = {}
        dept_counts: dict[str, int] = {}
        for emp in self.employees:
            d = emp["dept"]
            dept_counts[d] = dept_counts.get(d, 0) + 1
        for v in violations:
            emp_dept = next((e["dept"] for e in self.employees if e["id"]==v.employee_id), "Unknown")
            dept_violations[emp_dept] = dept_violations.get(emp_dept, 0) + 1
        scores = {}
        for dept, count in dept_counts.items():
            viol = dept_violations.get(dept, 0)
            scores[dept] = max(0, round(100 - (viol / count) * 50))
        return scores

    def _generate_recommendations(self, violations: list[ComplianceViolation]) -> list[str]:
        recs = []
        high = [v for v in violations if v.severity == "HIGH"]
        if len(high) > 3:
            recs.append(f"🚨 {len(high)} critical violations detected. Emergency HR review recommended.")
        overtime_violators = [v.employee_name for v in violations if v.violation_type == "Overtime Policy"]
        if overtime_violators:
            recs.append(f"📋 Overtime violations: {', '.join(overtime_violators[:3])}. Consider hiring or workload redistribution.")
        burnout_violators = [v.employee_name for v in violations if "Burnout" in v.violation_type]
        if burnout_violators:
            recs.append(f"🔥 Burnout critical: {', '.join(burnout_violators[:3])}. Mandatory wellness program enrollment.")
        return recs


# Singleton
compliance_agent = ComplianceAgent()
