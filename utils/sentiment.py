# utils/sentiment.py
"""
Sentiment & Emotion Analysis — Feature #14
Uses HuggingFace transformers (distilbert) locally.
No external API keys required.
"""

from dataclasses import dataclass
from typing import Optional
from loguru import logger

try:
    from transformers import pipeline as hf_pipeline
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    logger.warning("transformers not installed — using rule-based sentiment")


@dataclass
class SentimentResult:
    label: str          # POSITIVE / NEGATIVE / NEUTRAL
    score: float        # 0.0 to 1.0
    emotion: str        # Stress, Burnout, Disengagement, etc.
    alert_level: str    # HIGH / MODERATE / LOW / NONE
    alert_triggered: bool
    recommendation: str
    raw_score: float    # -1.0 to +1.0


class SentimentEngine:
    """
    Dual-mode sentiment engine:
      - Primary: HuggingFace distilbert (local, offline)
      - Fallback: Rule-based keyword analysis
    """

    NEGATIVE_KEYWORDS = [
        "stressed","stress","unhappy","frustrated","exhausted","tired","burnout",
        "burnt out","overworked","overwhelmed","depressed","anxious","worried",
        "unfair","demotivated","leaving","quit","resign","toxic","hostile",
        "ignored","undervalued","underpaid","unrecognized","hopeless",
    ]
    POSITIVE_KEYWORDS = [
        "happy","excited","motivated","great","excellent","love","enjoy",
        "proud","satisfied","appreciate","recognized","growing","promoted",
        "amazing","fantastic","thrilled","engaged","inspired",
    ]

    EMOTION_MAP = {
        "stress":       "Stress & Work Pressure",
        "burnout":      "Burnout",
        "quit":         "Flight Risk / Resignation Intent",
        "leaving":      "Flight Risk / Resignation Intent",
        "resign":       "Flight Risk / Resignation Intent",
        "overwhelmed":  "Overwhelm & Anxiety",
        "frustrated":   "Frustration",
        "unhappy":      "Disengagement",
        "unfair":       "Perceived Injustice",
        "undervalued":  "Recognition Gap",
        "anxious":      "Anxiety",
    }

    def __init__(self, model: str = "distilbert-base-uncased-finetuned-sst-2-english"):
        self.model_name = model
        self.pipe = None
        if HF_AVAILABLE:
            try:
                logger.info(f"Loading sentiment model: {model}")
                self.pipe = hf_pipeline("sentiment-analysis", model=model)
                logger.info("Sentiment model loaded successfully")
            except Exception as e:
                logger.warning(f"Could not load HF model: {e} — using fallback")

    def analyze(self, text: str) -> SentimentResult:
        if self.pipe:
            return self._hf_analyze(text)
        return self._rule_analyze(text)

    def _hf_analyze(self, text: str) -> SentimentResult:
        """HuggingFace transformer-based analysis."""
        try:
            result = self.pipe(text[:512])[0]
            label = result["label"]
            hf_score = result["score"]

            raw = hf_score if label == "POSITIVE" else -hf_score
            emotion = self._detect_emotion(text)
            alert_level, alert_triggered = self._compute_alert(raw, text)
            recommendation = self._get_recommendation(alert_level, emotion)

            return SentimentResult(
                label=label,
                score=hf_score,
                emotion=emotion,
                alert_level=alert_level,
                alert_triggered=alert_triggered,
                recommendation=recommendation,
                raw_score=round(raw, 3),
            )
        except Exception as e:
            logger.error(f"HF analysis failed: {e}")
            return self._rule_analyze(text)

    def _rule_analyze(self, text: str) -> SentimentResult:
        """Keyword-based fallback analysis."""
        lower = text.lower()
        neg_count = sum(1 for kw in self.NEGATIVE_KEYWORDS if kw in lower)
        pos_count = sum(1 for kw in self.POSITIVE_KEYWORDS if kw in lower)

        total = neg_count + pos_count
        if total == 0:
            raw = 0.0
            label = "NEUTRAL"
            score = 0.5
        elif neg_count > pos_count:
            raw = -(neg_count / total)
            label = "NEGATIVE"
            score = neg_count / total
        else:
            raw = pos_count / total
            label = "POSITIVE"
            score = pos_count / total

        emotion = self._detect_emotion(text)
        alert_level, alert_triggered = self._compute_alert(raw, text)
        recommendation = self._get_recommendation(alert_level, emotion)

        return SentimentResult(
            label=label,
            score=round(score, 3),
            emotion=emotion,
            alert_level=alert_level,
            alert_triggered=alert_triggered,
            recommendation=recommendation,
            raw_score=round(raw, 3),
        )

    def _detect_emotion(self, text: str) -> str:
        lower = text.lower()
        for keyword, emotion in self.EMOTION_MAP.items():
            if keyword in lower:
                return emotion
        return "General Negativity" if any(kw in lower for kw in self.NEGATIVE_KEYWORDS) else "Neutral"

    def _compute_alert(self, raw_score: float, text: str) -> tuple[str, bool]:
        lower = text.lower()
        high_risk_words = ["quit","resign","leaving","burnout","toxic","hopeless"]
        if any(w in lower for w in high_risk_words) or raw_score < -0.6:
            return "HIGH", True
        elif raw_score < -0.3:
            return "MODERATE", True
        elif raw_score < 0:
            return "LOW", False
        return "NONE", False

    def _get_recommendation(self, alert_level: str, emotion: str) -> str:
        recs = {
            "HIGH":     "Immediate: Schedule 1-on-1 with HRBP within 24 hours. Manager intervention required.",
            "MODERATE": "Within 1 week: Check-in meeting with manager. Consider workload review.",
            "LOW":      "Monitor over next 2 weeks. Include in next team engagement survey.",
            "NONE":     "Employee appears engaged and positive. No immediate action required.",
        }
        return recs.get(alert_level, "No action required.")


# Singleton
sentiment_engine = SentimentEngine()
