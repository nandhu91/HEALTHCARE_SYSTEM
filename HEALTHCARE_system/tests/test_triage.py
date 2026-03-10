"""
tests/test_triage.py
====================
Unit tests for triage_engine.py
Run: pytest tests/test_triage.py -v
"""

import pytest
from services.triage_engine import (
    classify_patient, classify_from_text,
    TriageResult, RED_FLAG_SYMPTOMS,
)


# ── Red-flag symptoms ────────────────────────────────────────────────────────

class TestRedFlagSymptoms:

    @pytest.mark.parametrize("symptom", list(RED_FLAG_SYMPTOMS))
    def test_each_red_flag_triggers_emergency(self, symptom):
        result = classify_patient([symptom])
        assert result.level   == "EMERGENCY"
        assert result.score   == 99
        assert result.priority == 1

    def test_red_flag_overrides_perfect_vitals(self):
        result = classify_patient(
            ["chest_pain"], temperature=98.6, o2_saturation=100.0, age_group="adult"
        )
        assert result.level == "EMERGENCY"

    def test_multiple_red_flags_still_emergency(self):
        result = classify_patient(["unconscious", "stroke_signs", "seizure"])
        assert result.level == "EMERGENCY"


# ── Temperature scoring ──────────────────────────────────────────────────────

class TestTemperature:

    def test_normal_temp_zero_score(self):
        assert classify_patient([], temperature=98.6).score == 0

    def test_high_temp_102_adds_1(self):
        assert classify_patient([], temperature=102.5).score == 1

    def test_critical_temp_104_adds_3(self):
        assert classify_patient([], temperature=104.0).score == 3

    def test_boundary_104_exactly(self):
        assert classify_patient([], temperature=104.0).score == 3

    def test_below_102_no_temp_score(self):
        assert classify_patient([], temperature=101.9).score == 0


# ── O2 saturation scoring ────────────────────────────────────────────────────

class TestO2Saturation:

    def test_normal_o2_zero_score(self):
        assert classify_patient([], o2_saturation=98.0).score == 0

    def test_low_o2_94_adds_2(self):
        assert classify_patient([], o2_saturation=93.0).score == 2

    def test_critical_o2_90_adds_3(self):
        assert classify_patient([], o2_saturation=88.0).score == 3

    def test_boundary_o2_90_exactly(self):
        assert classify_patient([], o2_saturation=90.0).score == 3

    def test_o2_91_adds_2_not_3(self):
        assert classify_patient([], o2_saturation=91.0).score == 2


# ── Age group scoring ────────────────────────────────────────────────────────

class TestAgeGroup:

    def test_adult_no_bonus(self):
        assert classify_patient([], age_group="adult").score == 0

    def test_child_adds_1(self):
        assert classify_patient([], age_group="child").score == 1

    def test_senior_adds_1(self):
        assert classify_patient([], age_group="senior").score == 1


# ── Combined scoring / emergency threshold ───────────────────────────────────

class TestCombinedScoring:

    def test_score_4_is_emergency(self):
        # 102.5°F(+1) + O2 93%(+2) + child(+1) = 4 → EMERGENCY
        result = classify_patient([], temperature=102.5, o2_saturation=93.0, age_group="child")
        assert result.level == "EMERGENCY"
        assert result.score == 4

    def test_score_3_is_normal(self):
        # 104°F (+3) adult → score=3 → NORMAL
        result = classify_patient([], temperature=104.0, o2_saturation=98.0, age_group="adult")
        assert result.level == "NORMAL"
        assert result.score == 3

    def test_score_5_is_emergency(self):
        # 104°F(+3) + O2 93%(+2) = 5 → EMERGENCY
        result = classify_patient([], temperature=104.0, o2_saturation=93.0)
        assert result.level == "EMERGENCY"
        assert result.score == 5

    def test_symptom_score_plus_vitals(self):
        # high_fever(+2) + O2 93%(+2) = 4 → EMERGENCY
        result = classify_patient(["high_fever"], o2_saturation=93.0)
        assert result.level == "EMERGENCY"


# ── Normal cases ─────────────────────────────────────────────────────────────

class TestNormalCases:

    def test_healthy_adult_normal(self):
        result = classify_patient(
            ["mild_cough"], temperature=98.6, o2_saturation=98.0, age_group="adult"
        )
        assert result.level == "NORMAL"

    def test_no_symptoms_normal(self):
        assert classify_patient([]).level == "NORMAL"

    def test_mild_symptoms_only_normal(self):
        result = classify_patient(["headache", "dizziness", "fatigue"])
        assert result.level == "NORMAL"

    def test_normal_result_priority_3(self):
        assert classify_patient([]).priority == 3

    def test_emergency_result_priority_1_or_2(self):
        result = classify_patient(["chest_pain"])
        assert result.priority <= 2


# ── Edge cases ───────────────────────────────────────────────────────────────

class TestEdgeCases:

    def test_empty_symptoms_list(self):
        result = classify_patient([])
        assert isinstance(result, TriageResult)
        assert result.score == 0

    def test_unknown_symptom_keys_ignored(self):
        result = classify_patient(["flying_elephants", "random_symptom_xyz"])
        assert result.level == "NORMAL"
        assert result.score == 0

    def test_duplicate_symptoms_counted_once(self):
        # high_fever twice should NOT double-count (list iteration)
        r1 = classify_patient(["high_fever"])
        r2 = classify_patient(["high_fever", "high_fever"])
        assert r1.score == r2.score

    def test_result_has_reasoning(self):
        result = classify_patient(["headache"])
        assert isinstance(result.reasoning, list)
        assert len(result.reasoning) > 0

    def test_to_dict_keys(self):
        d = classify_patient([]).to_dict()
        assert "level" in d and "score" in d and "priority" in d and "reasoning" in d


# ── classify_from_text ───────────────────────────────────────────────────────

class TestClassifyFromText:

    def test_chest_pain_text_emergency(self):
        result = classify_from_text("Patient reports chest pain and difficulty breathing")
        assert result.level == "EMERGENCY"

    def test_normal_text_normal(self):
        result = classify_from_text("Patient has a mild headache and slight dizziness")
        assert result.level == "NORMAL"

    def test_empty_text_normal(self):
        assert classify_from_text("").level == "NORMAL"

    def test_text_with_vitals(self):
        result = classify_from_text(
            "patient has high fever", temperature=104.5, o2_saturation=91.0
        )
        assert result.level == "EMERGENCY"

    def test_unconscious_text_emergency(self):
        result = classify_from_text("Patient is unconscious and not responding")
        assert result.level == "EMERGENCY"