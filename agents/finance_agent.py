# agents/finance_agent.py
"""
Finance / Payroll Agent — Feature #1 (Multi-Agent)
Handles payroll calculation, reimbursement validation, tax breakdown.
"""

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from loguru import logger


@dataclass
class PayslipResult:
    employee_name: str
    grade: str
    month: str
    gross: int
    basic: int
    hra: int
    special_allowance: int
    pf_employee: int
    pf_employer: int
    tds: int
    esi: int
    net_pay: int
    insights: list[str]


@dataclass
class ReimbursementResult:
    approved: bool
    amount: float
    category: str
    limit: float
    message: str
    audit_id: str


REIMBURSEMENT_LIMITS = {
    "domestic_travel": {"L1":5000,"L2":5000,"L3":8000,"L4":12000,"L5":12000,"L6":20000,"L7":20000},
    "international_travel": {"L1":0,"L2":0,"L3":15000,"L4":25000,"L5":25000,"L6":35000,"L7":35000},
    "conference": {"L1":5000,"L2":5000,"L3":10000,"L4":20000,"L5":20000,"L6":30000,"L7":30000},
    "medical": {"L1":3000,"L2":3000,"L3":5000,"L4":8000,"L5":8000,"L6":10000,"L7":10000},
}


class FinanceAgent:

    def __init__(self, db_path: str = "./hr_ai.db", employees_path: str = "./data/employees.json"):
        self.db_path = db_path
        with open(employees_path) as f:
            self.employees = {str(e["id"]): e for e in json.load(f)}
        self._init_tables()

    def _init_tables(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reimbursements (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                emp_id     TEXT NOT NULL,
                emp_name   TEXT NOT NULL,
                amount     REAL NOT NULL,
                category   TEXT NOT NULL,
                status     TEXT DEFAULT 'Pending',
                approved_by TEXT,
                timestamp  TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def generate_payslip(self, employee_id: str, month: str = None) -> PayslipResult:
        emp = self.employees.get(str(employee_id))
        if not emp:
            raise ValueError(f"Employee {employee_id} not found")

        if not month:
            month = datetime.now().strftime("%B %Y")

        gross = emp["salary"]
        basic = int(gross * 0.50)
        hra   = int(gross * 0.30)
        spec  = int(gross * 0.15)
        other = gross - basic - hra - spec

        pf_emp  = int(basic * 0.12)
        pf_er   = int(basic * 0.12)
        esi     = int(gross * 0.0075)
        tds     = self._compute_tds(gross)
        net     = gross - pf_emp - tds - esi

        tax_saving_opportunity = int(gross * 0.15)
        insights = [
            f"💡 Invest ₹{tax_saving_opportunity:,} in 80C instruments to save ₹{int(tax_saving_opportunity*0.3):,} in TDS",
            f"✅ PF compliance: 12% employee + 12% employer contribution applied",
            f"⚠️ Submit rent receipts to maximize HRA exemption of ₹{hra:,}",
        ]
        if emp["grade"] in ["L4","L5","L6","L7"]:
            insights.append("💼 Consider NPS Tier-II for additional 80CCD(1B) deduction of ₹50,000")

        logger.info(f"[FinanceAgent] Generated payslip for {emp['name']} — net: ₹{net:,}")

        return PayslipResult(
            employee_name=emp["name"],
            grade=emp["grade"],
            month=month,
            gross=gross,
            basic=basic,
            hra=hra,
            special_allowance=spec,
            pf_employee=pf_emp,
            pf_employer=pf_er,
            tds=tds,
            esi=esi,
            net_pay=net,
            insights=insights,
        )

    def _compute_tds(self, annual_gross: int) -> int:
        """Simple income tax slab computation (old regime)."""
        if annual_gross <= 250000:
            return 0
        elif annual_gross <= 500000:
            return int((annual_gross - 250000) * 0.05 / 12)
        elif annual_gross <= 1000000:
            return int((12500 + (annual_gross - 500000) * 0.20) / 12)
        else:
            return int((112500 + (annual_gross - 1000000) * 0.30) / 12)

    def validate_reimbursement(
        self,
        employee_id: str,
        amount: float,
        category: str = "domestic_travel",
    ) -> ReimbursementResult:
        emp = self.employees.get(str(employee_id))
        if not emp:
            return ReimbursementResult(False, amount, category, 0, "Employee not found", "")

        grade = emp.get("grade", "L3")
        limits = REIMBURSEMENT_LIMITS.get(category, REIMBURSEMENT_LIMITS["domestic_travel"])
        limit = limits.get(grade, 5000)

        approved = amount <= limit

        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "INSERT INTO reimbursements (emp_id,emp_name,amount,category,status,approved_by,timestamp) VALUES (?,?,?,?,?,?,?)",
            (str(employee_id), emp["name"], amount, category,
             "AI Approved" if approved else "Amount Exceeds Limit",
             "Finance Agent (AI)" if approved else "Rejected",
             datetime.now().isoformat()),
        )
        audit_id = f"RM-{cursor.lastrowid:05d}"
        conn.commit()
        conn.close()

        if approved:
            msg = f"✅ Reimbursement of ₹{amount:,.0f} approved. Limit for {grade}: ₹{limit:,}/day"
        else:
            msg = f"❌ Amount ₹{amount:,.0f} exceeds {grade} limit of ₹{limit:,}. Submit revised claim."

        logger.info(f"[FinanceAgent] Reimbursement {audit_id}: emp={emp['name']} amt=₹{amount} approved={approved}")
        return ReimbursementResult(approved, amount, category, limit, msg, audit_id)


# Singleton
finance_agent = FinanceAgent()
