# agents/recruitment_agent.py
"""
AI Recruitment Intelligence — Features #10 & #11
Resume scoring, skill matching, interview question generation, fit prediction.
Uses sentence-transformers for semantic skill matching (no API keys).
"""

import re
from dataclasses import dataclass, field
from typing import Optional
from loguru import logger

try:
    from sentence_transformers import SentenceTransformer, util
    ST_AVAILABLE = True
except ImportError:
    ST_AVAILABLE = False

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


@dataclass
class ResumeAnalysisResult:
    candidate_name: str
    job_title: str
    match_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    experience_years: int
    prediction: str
    interview_questions: list[str]
    recommendation: str


JD_SKILLS = {
    "Python Developer": ["Python","Django","FastAPI","PostgreSQL","Docker","Kubernetes","Redis","Kafka","REST API","Git"],
    "ML Engineer":      ["Python","TensorFlow","PyTorch","Scikit-learn","MLflow","Kubernetes","SQL","Spark","Feature Engineering"],
    "DevOps Engineer":  ["Docker","Kubernetes","Terraform","Ansible","AWS","Linux","CI/CD","Jenkins","Prometheus","Grafana"],
    "Data Engineer":    ["Python","Spark","Kafka","Airflow","SQL","AWS","Databricks","dbt","Hadoop"],
    "Frontend Dev":     ["React","TypeScript","JavaScript","CSS","HTML","Redux","GraphQL","Jest","Webpack"],
    "Product Manager":  ["Agile","Scrum","JIRA","Roadmap","OKRs","SQL","Figma","A/B Testing","Stakeholder Management"],
}

INTERVIEW_QUESTIONS = {
    "Python Developer": [
        "Explain Python's GIL and its impact on multi-threading.",
        "How does Python's memory management work? Explain garbage collection.",
        "Difference between generators and iterators with examples.",
        "Design a rate limiter that handles 10,000 requests/second.",
        "Explain async/await and the event loop in Python.",
        "How would you optimize a slow Django ORM query?",
        "Describe your experience with Docker and Kubernetes.",
        "How do you handle database migrations in production?",
    ],
    "ML Engineer": [
        "Explain the bias-variance tradeoff and how to balance it.",
        "How do you handle class imbalance in training data?",
        "Describe your MLOps pipeline from training to production.",
        "How would you detect and handle data drift in production?",
        "Explain transformer architecture and attention mechanism.",
        "How do you evaluate a recommendation system?",
        "Describe feature engineering techniques you've used.",
        "How do you ensure model fairness and mitigate bias?",
    ],
    "DevOps Engineer": [
        "Explain the difference between blue-green and canary deployments.",
        "How would you architect a Kubernetes cluster for high availability?",
        "Describe your experience with infrastructure as code.",
        "How do you handle secrets management in a cloud environment?",
        "Walk me through your CI/CD pipeline design.",
        "How do you approach capacity planning for a growing system?",
        "Describe a production incident you resolved — root cause and fix.",
    ],
}

BEHAVIORAL_QUESTIONS = [
    "Describe a time you disagreed with a technical decision. How did you handle it?",
    "Tell me about your biggest project failure and what you learned.",
    "How do you manage competing priorities under tight deadlines?",
    "Describe how you mentor junior team members.",
    "How do you stay updated with the latest technology trends?",
    "Tell me about a time you improved a team's engineering process.",
]


class RecruitmentAgent:

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.embed_model = None
        if ST_AVAILABLE:
            try:
                logger.info(f"Loading recruitment embedding model: {model_name}")
                self.embed_model = SentenceTransformer(model_name)
            except Exception as e:
                logger.warning(f"Could not load embedding model: {e}")

    def analyze_resume(
        self,
        candidate_name: str,
        resume_text: str,
        job_title: str = "Python Developer",
        experience_years: int = 3,
    ) -> ResumeAnalysisResult:
        required_skills = JD_SKILLS.get(job_title, JD_SKILLS["Python Developer"])

        # Skill matching
        if self.embed_model:
            matched, missing, score = self._semantic_match(resume_text, required_skills)
        else:
            matched, missing, score = self._keyword_match(resume_text, required_skills)

        # Prediction
        if score >= 0.85:
            prediction = "Excellent Fit — Recommend Fast-Track"
        elif score >= 0.70:
            prediction = "High Fit — Recommend Interview"
        elif score >= 0.55:
            prediction = "Moderate Fit — Conditional Interview"
        else:
            prediction = "Low Fit — Does not meet minimum requirements"

        # Generate interview questions
        tech_qs = INTERVIEW_QUESTIONS.get(job_title, INTERVIEW_QUESTIONS["Python Developer"])[:5]
        behavioral_qs = BEHAVIORAL_QUESTIONS[:3]
        all_questions = tech_qs + behavioral_qs

        recommendation = self._generate_recommendation(candidate_name, job_title, score, missing)

        logger.info(f"[RecruitmentAgent] {candidate_name} | {job_title} | score={score:.0%} | {prediction}")

        return ResumeAnalysisResult(
            candidate_name=candidate_name,
            job_title=job_title,
            match_score=round(score, 3),
            matched_skills=matched,
            missing_skills=missing,
            experience_years=experience_years,
            prediction=prediction,
            interview_questions=all_questions,
            recommendation=recommendation,
        )

    def _semantic_match(self, text: str, skills: list[str]) -> tuple[list,list,float]:
        try:
            text_emb  = self.embed_model.encode(text, convert_to_tensor=True)
            skill_embs = self.embed_model.encode(skills, convert_to_tensor=True)
            sims = util.cos_sim(skill_embs, text_emb).flatten().tolist()
            matched = [s for s, sim in zip(skills, sims) if sim > 0.45]
            missing = [s for s, sim in zip(skills, sims) if sim <= 0.45]
            score = len(matched) / len(skills) if skills else 0
            return matched, missing, score
        except Exception as e:
            logger.warning(f"Semantic match failed: {e}")
            return self._keyword_match(text, skills)

    def _keyword_match(self, text: str, skills: list[str]) -> tuple[list,list,float]:
        lower = text.lower()
        matched = [s for s in skills if s.lower() in lower]
        missing = [s for s in skills if s.lower() not in lower]
        score = len(matched) / len(skills) if skills else 0
        return matched, missing, score

    def _generate_recommendation(self, name: str, role: str, score: float, missing: list[str]) -> str:
        if missing:
            gaps = ", ".join(missing[:3])
            return f"{name} has a {score:.0%} match for {role}. Skill gaps: {gaps}. Consider training plan if hired."
        return f"{name} meets all requirements for {role}. Strong candidate — proceed to technical interview."

    def schedule_interview(self, candidate_name: str, role: str, date: str, panel: list[str]) -> dict:
        """Simulate interview scheduling — Feature #2 (Workflow Orchestration)."""
        logger.info(f"[RecruitmentAgent] Scheduling interview for {candidate_name}")
        return {
            "status": "scheduled",
            "candidate": candidate_name,
            "role": role,
            "date": date,
            "panel": panel,
            "questions_generated": len(INTERVIEW_QUESTIONS.get(role, BEHAVIORAL_QUESTIONS)),
            "ats_updated": True,
            "invites_sent": len(panel),
        }


# Singleton
recruitment_agent = RecruitmentAgent()
