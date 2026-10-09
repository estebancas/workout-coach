import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from workout_coach.models import Exercise, Routine, json_schemas

FIXTURE = Path(__file__).parent / "fixtures" / "routine.json"


def test_routine_json_round_trips_unchanged():
    raw = json.loads(FIXTURE.read_text())
    routine = Routine.model_validate(raw)
    assert routine.model_dump(mode="json") == raw


def test_group_format_is_enforced():
    with pytest.raises(ValidationError):
        Exercise(group="d1", name="x", sets_reps="3x10")


def test_unknown_fields_are_rejected():
    with pytest.raises(ValidationError):
        Exercise(group="A", name="x", sets_reps="3x10", weight=5)


def test_json_schemas_are_generated():
    schemas = json_schemas()
    assert "exercises" in schemas["DayRoutine"]["properties"]
    assert "injury" in schemas["Adjustment"]["properties"]
