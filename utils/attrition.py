# utils/attrition.py
"""
Predictive Attrition Intelligence — Feature #4
Uses scikit-learn RandomForest trained on mock data.
No external API keys required.
"""

import json
import numpy as np
from dataclasses import dataclass
from typing import Optional
from loguru import logger

try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.preprocessing import LabelEncoder, StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score
    SK_AVAILABLE = True
except ImportError:
    SK_AVAILABLE = False
    logger.warning("scikit-learn not installed — using rule-based attrition scoring")


@dataclass
class AttritionResult:
    employee_id: int
    employee_name: str
    risk_score: float        # 0.0 to 1.0
    risk_percent: int        # 0 to 100
    risk_level: str          # LOW / MODERATE / HIGH / CRITICAL
    signals: list[str]
    recommendation: str
    predicted_departure_days: Optional[int]


class AttritionEngine:
    """
    Attrition prediction pipeline:
    1. Feature engineering from employee data
    2. Train RandomForest on synthetic labeled data
    3. Predict risk score per employee
    4. Generate signals and intervention recommendations
    """

    RISK_SIGNALS = {
        "overtime_high":      (lambda e: e.get("overtime", 0) > 55,  "Overtime above 55hrs/week (burnout indicator)"),
        "low_leave":          (lambda e: (e.get("cl",0)+e.get("sl",0)+e.get("el",0)) < 10, "Very low leave balance used"),
        "negative_sentiment": (lambda e: e.get("sentiment", 0) < -0.2, "Negative sentiment detected in feedback"),
        "high_burnout":       (lambda e: e.get("burnout", 0) > 70,  "Burnout score above critical threshold"),
        "junior_grade":       (lambda e: e.get("grade","") in ["L1","L2"], "Junior grade — high market mobility"),
        "no_promotion":       (lambda e: e.get("years_since_promotion", 3) > 2, "No promotion in 2+ years"),
        "market_demand":      (lambda e: e.get("dept","") in ["Engineering","Data Science"], "High market demand for this skill set"),
    }

    INTERVENTIONS = {
        "CRITICAL": "🚨 Immediate HRBP intervention. Schedule exit-risk meeting within 48 hours. Consider counter-offer or role change.",
        "HIGH":     "⚠️ Manager + HR review within 1 week. Career growth discussion. Salary benchmark review.",
        "MODERATE": "📋 Quarterly check-in. Skill development plan. Recognition program enrollment.",
        "LOW":      "✅ Continue regular engagement. Include in wellness programs.",
    }

    def __init__(self, employees_path: str = "./data/employees.json"):
        self.employees: list[dict] = []
        self.model = None
        self.scaler = StandardScaler() if SK_AVAILABLE else None
        self._load_employees(employees_path)
        if SK_AVAILABLE:
            self._train_model()

    def _load_employees(self, path: str):
        try:
            with open(path) as f:
                self.employees = json.load(f)
            logger.info(f"Loaded {len(self.employees)} employees for attrition analysis")
        except Exception as e:
            logger.error(f"Failed to load employees: {e}")

    def _employee_to_features(self, emp: dict) -> list[float]:
        """Convert employee dict to ML feature vector."""
        grade_map = {"L1":1,"L2":2,"L3":3,"L4":4,"L5":5,"L6":6,"L7":7}
        dept_risk = {"Engineering":0.7,"Data Science":0.8,"DevOps":0.6,"Marketing":0.4,"HR":0.3,"Finance":0.4,"Product":0.6,"QA":0.5,"Legal":0.3,"Admin":0.2}
        return [
            emp.get("overtime", 45),
            emp.get("burnout", 40) / 100,
            emp.get("sentiment", 0.0),
            emp.get("salary", 80000) / 100000,
            grade_map.get(emp.get("grade","L3"), 3),
            (emp.get("cl",0) + emp.get("sl",0) + emp.get("el",0)) / 45,  # leave util
            dept_risk.get(emp.get("dept","Engineering"), 0.5),
        ]

    def _train_model(self):
        """Train on employee data using their pre-calculated risk as label."""
        if not self.employees:
            return
        X = np.array([self._employee_to_features(e) for e in self.employees])
        y = np.array([1 if e.get("risk", 30) > 50 else 0 for e in self.employees])

        X_scaled = self.scaler.fit_transform(X)

        self.model = RandomForestClassifier(
            n_estimators=100, max_depth=5, random_state=42
        )
        self.model.fit(X_scaled, y)
        preds = self.model.predict(X_scaled)
        logger.info(f"Attrition model trained — train accuracy: {accuracy_score(y, preds):.2%}")

    def predict(self, employee: dict) -> AttritionResult:
        """Predict attrition risk for a single employee."""
        # Compute ML score if available
        if SK_AVAILABLE and self.model:
            features = np.array([self._employee_to_features(employee)])
            features_scaled = self.scaler.transform(features)
            prob = self.model.predict_proba(features_scaled)[0][1]
        else:
            prob = employee.get("risk", 30) / 100

        # Blend ML score with explicit risk field
        explicit_risk = employee.get("risk", 30) / 100
        final_risk = (prob * 0.5 + explicit_risk * 0.5)

        # Detect active signals
        signals = [
            msg for key, (fn, msg) in self.RISK_SIGNALS.items()
            if fn(employee)
        ]

        risk_pct = int(final_risk * 100)
        if risk_pct >= 75:
            level = "CRITICAL"
        elif risk_pct >= 55:
            level = "HIGH"
        elif risk_pct >= 35:
            level = "MODERATE"
        else:
            level = "LOW"

        # Estimate departure timeline
        departure_days = None
        if level == "CRITICAL":
            departure_days = 30
        elif level == "HIGH":
            departure_days = 60
        elif level == "MODERATE":
            departure_days = 90

        return AttritionResult(
            employee_id=employee.get("id", 0),
            employee_name=employee.get("name", "Unknown"),
            risk_score=round(final_risk, 3),
            risk_percent=risk_pct,
            risk_level=level,
            signals=signals,
            recommendation=self.INTERVENTIONS[level],
            predicted_departure_days=departure_days,
        )

    def predict_all(self) -> list[AttritionResult]:
        """Predict attrition risk for all employees, sorted by risk descending."""
        results = [self.predict(e) for e in self.employees]
        return sorted(results, key=lambda r: -r.risk_score)

    def get_department_summary(self) -> dict:
        """Aggregate attrition risk by department."""
        dept_risks: dict[str, list[float]] = {}
        for emp in self.employees:
            dept = emp.get("dept", "Unknown")
            risk = emp.get("risk", 30) / 100
            dept_risks.setdefault(dept, []).append(risk)
        return {
            dept: {
                "avg_risk": round(np.mean(risks) * 100, 1),
                "max_risk": round(max(risks) * 100, 1),
                "headcount": len(risks),
                "high_risk_count": sum(1 for r in risks if r > 0.55),
            }
            for dept, risks in dept_risks.items()
        }


# Singleton
attrition_engine = AttritionEngine()
