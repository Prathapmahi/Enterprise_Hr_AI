# workflows/definitions.py
"""
Pre-defined Enterprise Workflow Definitions — Feature #2
Each workflow maps to a sequence of agent actions.
"""

from workflows.engine import workflow_engine, WorkflowResult


def run_interview_scheduling_workflow(
    candidate_name: str,
    role: str,
    date: str,
    panel: list[str],
) -> WorkflowResult:
    """
    Schedule Python Developer Interview — 7 automated steps.
    Orchestrator → Recruitment → Calendar → Notify → ATS → Reminder
    """
    steps = [
        {"name": "Check panel availability",     "agent": "calendar_agent",    "fn": lambda: {"available": True, "panelists": panel}},
        {"name": "Create meeting event",         "agent": "calendar_agent",    "fn": lambda: {"event_id": "EVT-001", "meeting_link": "https://teams.microsoft.com/meet/abc123"}},
        {"name": "Send invites to panelists",    "agent": "notify_agent",      "fn": lambda: {"sent_to": panel, "channels": ["email"]}},
        {"name": "Generate interview questions", "agent": "recruitment_agent", "fn": lambda: {"questions_generated": 11, "role": role}},
        {"name": "Update ATS system",            "agent": "recruitment_agent", "fn": lambda: {"ats_status": "Interview Scheduled", "candidate": candidate_name}},
        {"name": "Send candidate confirmation",  "agent": "notify_agent",      "fn": lambda: {"sent_to": candidate_name, "date": date}},
        {"name": "Set reminder notification",    "agent": "notify_agent",      "fn": lambda: {"reminder_set": "30 minutes before", "channels": ["email","sms"]}},
    ]
    return workflow_engine.execute("Interview Scheduling", steps, {"candidate": candidate_name, "role": role})


def run_onboarding_workflow(emp_name: str, email: str, dept: str, doj: str) -> WorkflowResult:
    """
    Autonomous Onboarding — Feature #15 — 9 automated steps.
    """
    first = emp_name.split()[0].lower()
    steps = [
        {"name": f"Create email: {first}@company.com",  "agent": "it_agent",       "fn": lambda: {"email": f"{first}@company.com", "created": True}},
        {"name": "Submit laptop request",               "agent": "it_agent",       "fn": lambda: {"ticket_id": "IT-2024-892", "asset": "Dell Latitude 5540"}},
        {"name": "Generate Employee ID",                "agent": "hrms_agent",     "fn": lambda: {"emp_id": "EMP-2024-046", "name": emp_name}},
        {"name": "Activate payroll record",             "agent": "finance_agent",  "fn": lambda: {"payroll_active": True, "first_salary": doj[:7]}},
        {"name": "Schedule Day-1 induction",            "agent": "calendar_agent", "fn": lambda: {"induction_date": doj, "buddy_assigned": "Existing colleague"}},
        {"name": "Create Teams & Slack accounts",       "agent": "it_agent",       "fn": lambda: {"teams": f"{first}@company.com", "slack": f"@{first}"}},
        {"name": "Assign LMS onboarding modules",       "agent": "lms_agent",      "fn": lambda: {"modules": ["Company Intro","Code of Conduct","Security Training","Benefits Overview"], "deadline": "30 days"}},
        {"name": "Notify reporting manager",            "agent": "notify_agent",   "fn": lambda: {"manager_notified": True, "joining_date": doj}},
        {"name": "Generate welcome kit",                "agent": "hr_agent",       "fn": lambda: {"welcome_email_sent": True, "kit": ["Badge","Handbook","IT setup guide"]}},
    ]
    return workflow_engine.execute("New Employee Onboarding", steps, {"emp_name": emp_name, "dept": dept})


def run_offboarding_workflow(emp_name: str, emp_id: str, last_date: str) -> WorkflowResult:
    """
    Employee Exit / Offboarding — Feature #19 (Cross-System AI) — 7 steps.
    """
    steps = [
        {"name": "Update HRMS status to Resigned",      "agent": "hrms_agent",     "fn": lambda: {"status": "Resigned", "effective": last_date}},
        {"name": "Disable Active Directory account",    "agent": "it_agent",       "fn": lambda: {"ad_disabled": True, "accounts": ["email","VPN","SSO"]}},
        {"name": "Revoke application access",           "agent": "it_agent",       "fn": lambda: {"revoked": ["JIRA","GitHub","AWS","Slack"]}},
        {"name": "Notify IT for device collection",     "agent": "notify_agent",   "fn": lambda: {"it_ticket": "IT-EX-001", "device": "Laptop + accessories"}},
        {"name": "Generate Full & Final settlement",    "agent": "finance_agent",  "fn": lambda: {"ff_amount": "Calculated", "notice_period": "Served/Buyout"}},
        {"name": "Schedule exit interview",             "agent": "calendar_agent", "fn": lambda: {"exit_interview": True, "with": "HRBP", "date": last_date}},
        {"name": "Issue relieving letter",              "agent": "hr_agent",       "fn": lambda: {"letter_issued": True, "within_days": 30}},
    ]
    return workflow_engine.execute("Employee Offboarding", steps, {"emp_name": emp_name, "emp_id": emp_id})


def run_performance_review_workflow(cycle_year: str) -> WorkflowResult:
    """Annual Performance Review Cycle — 6 steps."""
    steps = [
        {"name": "Pull KPI data from HRMS",             "agent": "hrms_agent",     "fn": lambda: {"employees_covered": 45, "kpis_extracted": True}},
        {"name": "Calculate weighted scores",           "agent": "analytics_agent","fn": lambda: {"avg_score": 3.2, "distribution": {"5":10,"4":20,"3":60,"1-2":10}}},
        {"name": "Generate draft appraisal letters",    "agent": "hr_agent",       "fn": lambda: {"letters_generated": 45, "ai_assisted": True}},
        {"name": "Send to managers for review",         "agent": "notify_agent",   "fn": lambda: {"managers_notified": 12, "deadline": f"{cycle_year}-03-31"}},
        {"name": "Collect employee sign-offs",          "agent": "hrms_agent",     "fn": lambda: {"sign_off_portal": "Active", "deadline": f"{cycle_year}-04-15"}},
        {"name": "Update compensation system",          "agent": "finance_agent",  "fn": lambda: {"increments_processed": 45, "effective": f"{cycle_year}-04-01"}},
    ]
    return workflow_engine.execute("Performance Review Cycle", steps, {"year": cycle_year})


def run_compliance_audit_workflow() -> WorkflowResult:
    """Compliance Audit — Feature #16 — 6 steps."""
    steps = [
        {"name": "Pull attendance data for 45 employees","agent": "hrms_agent",     "fn": lambda: {"records_pulled": 45, "period": "Last 90 days"}},
        {"name": "Run policy rule engine",              "agent": "compliance_agent","fn": lambda: {"rules_checked": 5, "employees_scanned": 45}},
        {"name": "Flag policy violations",              "agent": "compliance_agent","fn": lambda: {"violations_found": 8, "critical": 3}},
        {"name": "Generate compliance report",          "agent": "analytics_agent", "fn": lambda: {"report_id": "CR-2024-Q2", "pages": 12}},
        {"name": "Notify department heads",             "agent": "notify_agent",    "fn": lambda: {"depts_notified": 7, "channels": ["email"]}},
        {"name": "Archive audit record",                "agent": "hrms_agent",      "fn": lambda: {"archived": True, "retention_years": 7}},
    ]
    return workflow_engine.execute("Compliance Audit", steps, {})
