import pytest
from pydantic import ValidationError

from workout_coach.profile import DEFAULT_PATH, AthleteProfile, load_profile


def test_athlete_yaml_validates():
    profile = load_profile(DEFAULT_PATH)
    assert profile.language == "es"
    assert any(i.area == "knee" and i.side == "left" for i in profile.injuries)


def test_invalid_status_is_rejected():
    with pytest.raises(ValidationError):
        AthleteProfile.model_validate(
            {
                "language": "es",
                "context": {"occupation": "x", "goals": [], "equipment": "x"},
                "policy": {"conflicts": "substitute", "on_pain": "pain_scale"},
                "injuries": [
                    {"area": "knee", "side": "left", "diagnosis": "x", "status": "bad"}
                ],
            }
        )
