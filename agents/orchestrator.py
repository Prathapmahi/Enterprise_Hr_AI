# agents/orchestrator.py
"""
Orchestrator Agent — Feature #1 (Multi-Agent System), Feature #6 (Context-Aware Reasoning)
Routes incoming requests to specialized agents.
Uses Ollama (local LLM) or rule-based intent detection.
"""

import re
from dataclasses import dataclass
from typing import Optional
from loguru import logger
from datetime import datetime

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


@dataclass
class AgentRoute:
    agent: str
    intent: str
    entities: dict
    confidence: float


class OrchestratorAgent:
    """
    Intent detection + routing engine.
    Dual mode: Ollama LLM (preferred) → keyword fallback.
    """

    INTENT_PATTERNS = {
        "leave_apply":      [r"apply.*(leave|sick|casual|vacation)", r"take.*(leave|day off)", r"sick.*tomorrow"],
        "leave_balance":    [r"leave balance", r"how many.*leaves", r"remaining.*leave"],
        "leave_cancel":     [r"cancel.*leave", r"withdraw.*leave"],
        "leave_status":     [r"leave.*status", r"leave.*approved"],
        "payslip":          [r"payslip", r"salary.*slip", r"pay.*statement"],
        "salary":           [r"(my |the )?salary", r"how much.*earn", r"ctc"],
        "reimbursement":    [r"reimburs", r"claim.*expense", r"travel.*expense"],
        "policy_query":     [r"policy", r"rule", r"entitled", r"maternity", r"paternity", r"notice period"],
        "attrition":        [r"attrition", r"resignation risk", r"who.*leaving"],
        "burnout":          [r"burnout", r"stress.*level", r"overwork"],
        "interview":        [r"schedule.*interview", r"interview.*tomorrow", r"book.*interview"],
        "onboarding":       [r"onboard", r"new.*employee", r"joining"],
        "offboarding":      [r"resign", r"exit", r"offboard", r"full.*final"],
        "compliance":       [r"compliance", r"violation", r"attendance.*issue"],
        "analytics":        [r"analytics", r"dashboard", r"report", r"forecast", r"predict.*hiring"],
        "sentiment":        [r"feedback.*analysis", r"sentiment", r"emotion.*detect"],
    }

    AGENT_MAP = {
        "leave_apply":    "leave_agent",
        "leave_balance":  "leave_agent",
        "leave_cancel":   "leave_agent",
        "leave_status":   "leave_agent",
        "payslip":        "finance_agent",
        "salary":         "finance_agent",
        "reimbursement":  "finance_agent",
        "policy_query":   "rag_agent",
        "attrition":      "attrition_agent",
        "burnout":        "burnout_agent",
        "interview":      "recruitment_agent",
        "onboarding":     "onboarding_agent",
        "offboarding":    "compliance_agent",
        "compliance":     "compliance_agent",
        "analytics":      "analytics_agent",
        "sentiment":      "sentiment_agent",
    }

    def __init__(self, ollama_model: str = "llama3"):
        self.ollama_model = ollama_model

    def detect_intent(self, message: str) -> AgentRoute:
        """Detect intent using LLM or regex fallback."""
        if OLLAMA_AVAILABLE:
            return self._llm_detect(message)
        return self._regex_detect(message)

    def _llm_detect(self, message: str) -> AgentRoute:
        """Use local Ollama LLM for intent detection."""
        intents = list(self.INTENT_PATTERNS.keys())
        prompt = f"""Classify this HR request into ONE of these intents: {', '.join(intents)}
Also extract key entities (employee name, leave type, date, amount).
Respond ONLY as JSON: {{"intent": "...", "entities": {{}}, "confidence": 0.9}}

Request: {message}"""
        try:
            resp = ollama.chat(
                model=self.ollama_model,
                messages=[{"role":"user","content":prompt}],
                format="json",
            )
            import json
            data = json.loads(resp["message"]["content"])
            intent = data.get("intent", "unknown")
            return AgentRoute(
                agent=self.AGENT_MAP.get(intent, "orchestrator"),
                intent=intent,
                entities=data.get("entities", {}),
                confidence=data.get("confidence", 0.9),
            )
        except Exception as e:
            logger.warning(f"Ollama intent detection failed: {e} — using regex")
            return self._regex_detect(message)

    def _regex_detect(self, message: str) -> AgentRoute:
        """Regex-based intent detection fallback."""
        lower = message.lower()
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, lower):
                    entities = self._extract_entities(message, intent)
                    return AgentRoute(
                        agent=self.AGENT_MAP.get(intent, "orchestrator"),
                        intent=intent,
                        entities=entities,
                        confidence=0.85,
                    )
        return AgentRoute(agent="orchestrator", intent="general", entities={}, confidence=0.4)

    def _extract_entities(self, message: str, intent: str) -> dict:
        """Extract named entities from message."""
        entities = {}
        # Leave type
        for lt in ["sick","casual","earned","maternity","paternity","lop"]:
            if lt in message.lower():
                entities["leave_type"] = lt.title() + " Leave"
                break
        # Amount
        amt = re.search(r"₹?\s*(\d[\d,]+)", message)
        if amt:
            entities["amount"] = amt.group(1).replace(",","")
        # Date keywords
        for d in ["tomorrow","today","monday","tuesday","wednesday","thursday","friday"]:
            if d in message.lower():
                entities["date"] = d
                break
        return entities

    def route(self, message: str, employee_context: dict = None) -> dict:
        """
        Full routing with context enrichment.
        Returns routing decision + context for the target agent.
        """
        route = self.detect_intent(message)
        logger.info(
            f"[Orchestrator] intent={route.intent} agent={route.agent} "
            f"confidence={route.confidence:.2f} entities={route.entities}"
        )
        return {
            "agent": route.agent,
            "intent": route.intent,
            "entities": route.entities,
            "confidence": route.confidence,
            "employee_context": employee_context or {},
            "timestamp": datetime.now().isoformat(),
        }


# Singleton
orchestrator = OrchestratorAgent()
