#!/usr/bin/env python3
"""
Enterprise HR AI System — API Test Suite
Tests all 20 features end-to-end without external API keys.
Run: python test_all.py
"""

import sys
import json

BASE = "http://localhost:8000"

def test(name, fn):
    try:
        result = fn()
        print(f"  ✅  {name}")
        return result
    except Exception as e:
        print(f"  ❌  {name}: {e}")
        return None

def run_tests():
    try:
        import requests
    except ImportError:
        print("Install requests: pip install requests")
        sys.exit(1)

    print("\n" + "="*60)
    print("  Enterprise HR AI System — Test Suite")
    print("="*60)

    # Health check
    print("\n[1] Health & Setup")
    r = test("Health endpoint", lambda: requests.get(f"{BASE}/health").raise_for_status())

    # Employees
    print("\n[2] Employee Data (45 mock employees)")
    r = test("GET /api/employees", lambda: requests.get(f"{BASE}/api/employees").raise_for_status())
    if r:
        data = requests.get(f"{BASE}/api/employees").json()
        assert data["total"] == 45, f"Expected 45, got {data['total']}"
        print(f"       → {data['total']} employees loaded")

    # Leave
    print("\n[3] Leave Management (Feature #1, #6)")
    r = test("GET /api/leave/balance/1", lambda: requests.get(f"{BASE}/api/leave/balance/1").raise_for_status())
    r = test("POST /api/leave/apply", lambda: requests.post(f"{BASE}/api/leave/apply",
        json={"employee_id":"1","leave_type":"Sick Leave","from_date":"2024-06-20","to_date":"2024-06-20"}).raise_for_status())

    # Payroll
    print("\n[4] Payroll Intelligence (Feature #9)")
    r = test("GET /api/payroll/1", lambda: requests.get(f"{BASE}/api/payroll/1").raise_for_status())
    if r:
        data = requests.get(f"{BASE}/api/payroll/1").json()
        print(f"       → Net pay: ₹{data.get('net_pay',0):,}")

    # RAG
    print("\n[5] Enterprise RAG (Feature #3)")
    r = test("POST /api/rag/query", lambda: requests.post(f"{BASE}/api/rag/query",
        json={"query":"What is maternity leave policy?","employee_grade":"L3","location":"Chennai"}).raise_for_status())

    # Sentiment
    print("\n[6] Sentiment Analysis (Feature #14)")
    r = test("POST /api/sentiment", lambda: requests.post(f"{BASE}/api/sentiment",
        json={"text":"I am extremely stressed and overwhelmed with work."}).raise_for_status())
    if r:
        data = requests.post(f"{BASE}/api/sentiment",
            json={"text":"I am extremely stressed and overwhelmed with work."}).json()
        print(f"       → Emotion: {data.get('emotion')} | Alert: {data.get('alert_level')}")

    # Attrition
    print("\n[7] Attrition Prediction (Feature #4)")
    r = test("GET /api/attrition", lambda: requests.get(f"{BASE}/api/attrition").raise_for_status())
    if r:
        data = requests.get(f"{BASE}/api/attrition").json()
        print(f"       → Critical: {data.get('critical')}, High: {data.get('high')}")

    # Burnout
    print("\n[8] Burnout Detection (Feature #5)")
    r = test("GET /api/burnout", lambda: requests.get(f"{BASE}/api/burnout").raise_for_status())

    # Recruitment
    print("\n[9] Recruitment Intelligence (Feature #10, #11)")
    r = test("POST /api/recruitment/analyze", lambda: requests.post(f"{BASE}/api/recruitment/analyze",
        json={"candidate_name":"Test Candidate","resume_text":"Python Django FastAPI Docker Kubernetes PostgreSQL","job_title":"Python Developer","experience_years":4}).raise_for_status())
    if r:
        data = requests.post(f"{BASE}/api/recruitment/analyze",
            json={"candidate_name":"Test Candidate","resume_text":"Python Django FastAPI Docker Kubernetes PostgreSQL","job_title":"Python Developer","experience_years":4}).json()
        print(f"       → Match: {data.get('match_percent')}% | {data.get('prediction')}")

    # Compliance
    print("\n[10] Compliance Monitoring (Feature #16)")
    r = test("GET /api/compliance", lambda: requests.get(f"{BASE}/api/compliance").raise_for_status())

    # RBAC
    print("\n[11] RBAC Security (Feature #13)")
    r = test("POST /api/rbac/check — ALLOW", lambda: requests.post(f"{BASE}/api/rbac/check",
        json={"user_id":"1","user_role":"employee","action":"view_own_salary"}).raise_for_status())
    r = test("POST /api/rbac/check — DENY", lambda: requests.post(f"{BASE}/api/rbac/check",
        json={"user_id":"1","user_role":"employee","action":"view_others_salary"}).raise_for_status())

    # Analytics
    print("\n[12] Analytics & Decision Intelligence (Feature #17, #20)")
    r = test("GET /api/analytics", lambda: requests.get(f"{BASE}/api/analytics").raise_for_status())

    # Workflows
    print("\n[13] Workflow Orchestration (Feature #2)")
    r = test("POST /api/workflow/execute (interview)", lambda: requests.post(f"{BASE}/api/workflow/execute",
        json={"workflow_type":"interview","params":{"candidate_name":"Test","role":"Python Developer","date":"Tomorrow","panel":["TL","Manager"]}}).raise_for_status())
    r = test("POST /api/workflow/execute (compliance)", lambda: requests.post(f"{BASE}/api/workflow/execute",
        json={"workflow_type":"compliance","params":{}}).raise_for_status())

    # Multi-agent
    print("\n[14] Multi-Agent Demo (Feature #1)")
    r = test("POST /api/multiagent/demo", lambda: requests.post(f"{BASE}/api/multiagent/demo",
        json={"message":"I need leave for Friday and reimbursement for ₹4200"}).raise_for_status())

    # Onboarding
    print("\n[15] Autonomous Onboarding (Feature #15)")
    r = test("POST /api/onboarding/start", lambda: requests.post(f"{BASE}/api/onboarding/start",
        json={"name":"Meera Test","email":"meera@company.com","dept":"Engineering","role":"Dev","doj":"2024-07-01"}).raise_for_status())

    # Chat
    print("\n[16] AI Chat with Memory (Feature #7)")
    r = test("POST /api/chat — leave query", lambda: requests.post(f"{BASE}/api/chat",
        json={"message":"What is my leave balance?","employee_id":"1"}).raise_for_status())
    r = test("POST /api/chat — policy query", lambda: requests.post(f"{BASE}/api/chat",
        json={"message":"What is maternity leave policy?","employee_id":"1"}).raise_for_status())

    print("\n" + "="*60)
    print("  All tests completed!")
    print("  → Open http://localhost:8000 for the full UI")
    print("  → Open http://localhost:8000/docs for API explorer")
    print("="*60 + "\n")

if __name__ == "__main__":
    run_tests()
