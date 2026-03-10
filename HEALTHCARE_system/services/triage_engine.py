"""
services/triage_engine.py
=========================
Core Python triage classification engine.

Rules:
  1. Red-flag symptoms → instant EMERGENCY (score=99, priority=1)
  2. Vital signs: temperature + O2 saturation add to score
  3. Age vulnerability: child/senior +1 point
  4. Score >= 4 → EMERGENCY, else NORMAL
"""

from dataclasses import dataclass, field
from typing import List


# ---------------------------------------------------------------------------
# Symptom definitions
# ---------------------------------------------------------------------------

RED_FLAG_SYMPTOMS = {
    "chest_pain",
    "difficulty_breathing",
    "unconscious",
    "severe_bleeding",
    "stroke_signs",
    "anaphylaxis",
    "cardiac_arrest",
    "severe_head_injury",
    "paralysis",
    "seizure",
}

SYMPTOM_SCORES = {
    "high_fever":     2,
    "vomiting_blood": 3,
    "severe_pain":    2,
    "confusion":      2,
    "fracture":       2,
    "dizziness":      1,
    "vomiting":       1,
    "headache":       1,
    "mild_cough":     0,
    "mild_fever":     0,
    "fatigue":        0,
    "runny_nose":     0,
}

# Vital thresholds
TEMP_CRITICAL      = 104.0
TEMP_HIGH          = 102.0
O2_CRITICAL        = 90.0
O2_LOW             = 94.0
EMERGENCY_THRESHOLD = 4


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class TriageResult:
    level:     str
    score:     int
    reasoning: List[str] = field(default_factory=list)
    priority:  int = 3       # 1=critical … 5=routine

    def to_dict(self):
        return {
            "level":     self.level,
            "score":     self.score,
            "priority":  self.priority,
            "reasoning": self.reasoning,
        }


# ---------------------------------------------------------------------------
# Core classification
# ---------------------------------------------------------------------------

def classify_patient(
    symptoms:      List[str],
    temperature:   float = 98.6,
    o2_saturation: float = 98.0,
    age_group:     str   = "adult",
) -> TriageResult:
    """
    Classify a patient as NORMAL or EMERGENCY.

    Parameters
    ----------
    symptoms      : list of symptom keys
    temperature   : body temperature in Fahrenheit
    o2_saturation : blood oxygen saturation in %
    age_group     : 'adult' | 'child' | 'senior'

    Returns
    -------
    TriageResult
    """
    reasoning: List[str] = []
    score: int = 0

    # Step 1 — Red-flag check
    for s in symptoms:
        if s in RED_FLAG_SYMPTOMS:
            reasoning.append(
                f"RED FLAG: '{s}' is a life-threatening symptom → immediate EMERGENCY."
            )
            return TriageResult(level="EMERGENCY", score=99, reasoning=reasoning, priority=1)

    # Step 2 — Symptom scoring
    for s in symptoms:
        pts = SYMPTOM_SCORES.get(s, 0)
        if pts > 0:
            score += pts
            reasoning.append(f"Symptom '{s}' → +{pts} point(s).")

    # Step 3 — Temperature
    if temperature >= TEMP_CRITICAL:
        score += 3
        reasoning.append(f"Critical temperature {temperature}°F (≥{TEMP_CRITICAL}) → +3 points.")
    elif temperature >= TEMP_HIGH:
        score += 1
        reasoning.append(f"High temperature {temperature}°F (≥{TEMP_HIGH}) → +1 point.")
    else:
        reasoning.append(f"Temperature {temperature}°F is within safe range.")

    # Step 4 — O2 saturation
    if o2_saturation <= O2_CRITICAL:
        score += 3
        reasoning.append(f"Critical O2 saturation {o2_saturation}% (≤{O2_CRITICAL}%) → +3 points.")
    elif o2_saturation <= O2_LOW:
        score += 2
        reasoning.append(f"Low O2 saturation {o2_saturation}% (≤{O2_LOW}%) → +2 points.")
    else:
        reasoning.append(f"O2 saturation {o2_saturation}% is acceptable.")

    # Step 5 — Age vulnerability
    if age_group in ("child", "senior"):
        score += 1
        reasoning.append(f"Age group '{age_group}' → +1 vulnerability point.")

    # Step 6 — Decision
    reasoning.append(f"Total score: {score} | Threshold: {EMERGENCY_THRESHOLD}.")

    if score >= EMERGENCY_THRESHOLD:
        reasoning.append("DECISION: EMERGENCY — score meets threshold.")
        return TriageResult(level="EMERGENCY", score=score, reasoning=reasoning, priority=2)
    else:
        reasoning.append("DECISION: NORMAL — standard queue.")
        return TriageResult(level="NORMAL", score=score, reasoning=reasoning, priority=3)


# ---------------------------------------------------------------------------
# Free-text classification (auto-extracts keywords)
# ---------------------------------------------------------------------------

KEYWORD_MAP = {
    "chest pain":          "chest_pain",
    "shortness of breath": "difficulty_breathing",
    "breathing":           "difficulty_breathing",
    "unconscious":         "unconscious",
    "bleeding":            "severe_bleeding",
    "stroke":              "stroke_signs",
    "allergic":            "anaphylaxis",
    "cardiac arrest":      "cardiac_arrest",
    "seizure":             "seizure",
    "paralysis":           "paralysis",
    "high fever":          "high_fever",
    "severe pain":         "severe_pain",
    "vomiting blood":      "vomiting_blood",
    "confusion":           "confusion",
    "fracture":            "fracture",
    "dizziness":           "dizziness",
    "headache":            "headache",
    "vomiting":            "vomiting",
}


def classify_from_text(
    text:          str,
    temperature:   float = 98.6,
    o2_saturation: float = 98.0,
    age_group:     str   = "adult",
) -> TriageResult:
    """Classify from a free-text symptom description."""
    text_lower = text.lower()
    symptoms   = []
    for keyword, key in KEYWORD_MAP.items():
        if keyword in text_lower and key not in symptoms:
            symptoms.append(key)
    return classify_patient(symptoms, temperature, o2_saturation, age_group)