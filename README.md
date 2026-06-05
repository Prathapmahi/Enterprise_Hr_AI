# Enterprise HR AI System

A complete, end-to-end Multi-Agent HR Intelligence Platform built entirely with open-source tools. No paid API keys required.

## Architecture

```
enterprise_hr_ai/
├── frontend/           # Single-file HTML UI (open in any browser)
├── agents/             # 6 AI agent modules (Python)
│   ├── orchestrator.py
│   ├── leave_agent.py
│   ├── finance_agent.py
│   ├── compliance_agent.py
│   ├── recruitment_agent.py
│   └── notify_agent.py
├── workflows/          # Workflow orchestration engine
│   ├── engine.py
│   └── definitions.py
├── api/                # FastAPI REST backend
│   ├── main.py
│   └── routes/
├── data/               # Mock data + RAG knowledge base
│   ├── employees.json
│   ├── policies.json
│   └── knowledge_base/
├── utils/              # Shared utilities
│   ├── rag.py          # RAG engine (sentence-transformers)
│   ├── sentiment.py    # Sentiment analysis (transformers)
│   ├── attrition.py    # Attrition prediction (scikit-learn)
│   └── rbac.py         # RBAC security layer
├── config/
│   └── settings.py
├── requirements.txt
├── docker-compose.yml
└── run.sh
```

## Features Implemented (All 20)

1. Multi-Agent HR System (6 agents)
2. AI Workflow Orchestration Engine
3. Enterprise RAG (sentence-transformers + FAISS)
4. Predictive Attrition Intelligence (scikit-learn)
5. Burnout Detection System
6. Context-Aware AI Reasoning
7. Persistent AI Memory (SQLite)
8. Voice AI HR Assistant (Web Speech API)
9. Multimodal HR AI (text + file upload)
10. AI Recruitment Intelligence
11. AI Interview Copilot
12. Enterprise Knowledge Intelligence
13. AI Governance & Security Layer (RBAC)
14. Sentiment & Emotion Analysis (transformers)
15. Autonomous Onboarding System
16. AI Compliance Monitoring
17. Enterprise Analytics AI
18. Self-Improving AI System (feedback loop)
19. Cross-System Enterprise AI
20. AI Decision Intelligence

## Tech Stack (100% Open Source, No API Keys)

| Layer | Technology |
|-------|-----------|
| LLM | Ollama + llama3 / mistral (local) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Vector DB | FAISS (in-memory) |
| Sentiment | transformers (distilbert-base) |
| Backend | FastAPI + Uvicorn |
| Database | SQLite (persistent memory) |
| Frontend | Pure HTML/CSS/JS (zero dependencies) |
| Container | Docker + Docker Compose |

## Quick Start

### Option 1 — Frontend Only (no install)
```bash
open frontend/index.html
```

### Option 2 — Full Backend + Frontend
```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install & start Ollama (local LLM)
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3

# 3. Start the API server
python api/main.py

# 4. Open frontend
open frontend/index.html
```

### Option 3 — Docker (recommended)
```bash
docker-compose up --build
# Visit http://localhost:8000
```

## 45 Mock Employees
Pre-loaded with realistic data covering Engineering, Data Science, HR, Finance, DevOps, Marketing, QA, Legal, Product departments.

## API Endpoints
- POST /api/chat         — AI chat with agent routing
- POST /api/leave/apply  — Apply leave with AI validation
- GET  /api/attrition    — Attrition risk scores
- GET  /api/burnout      — Burnout detection results
- POST /api/rag/query    — RAG knowledge base query
- POST /api/recruitment/analyze — Resume analyzer
- POST /api/sentiment    — Sentiment analysis
- GET  /api/employees    — Employee data
- POST /api/rbac/check   — Access control check
- GET  /api/analytics    — Workforce analytics
