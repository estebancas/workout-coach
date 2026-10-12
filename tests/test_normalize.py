from datetime import date

import pytest

from workout_coach.normalize import normalize, parse_info


@pytest.mark.parametrize(
    ("info", "expected"),
    [
        ("3x12", ("3x12", [])),
        (
            "3x20 reps\npasos largos y profundos ",
            ("3x20 reps", ["pasos largos y profundos"]),
        ),
        ("3x10 por lado\ntrabaja de lado", ("3x10 por lado", ["trabaja de lado"])),
        ("4x12 pausa 1 seg en el pecho", ("4x12", ["pausa 1 seg en el pecho"])),
        ("3x8-12", ("3x8-12", [])),
        ("3x 45 segundos", ("3x 45 segundos", [])),
        ("2x12\n2x8\n", ("2x12, 2x8", [])),
        ("x315 puede trabajarlo unilateral", ("x315 puede trabajarlo unilateral", [])),
        ("3 sets al fallo max 12 reps", ("3 sets al fallo max 12 reps", [])),
        ("", ("", [])),
    ],
)
def test_parse_info(info, expected):
    assert parse_info(info) == expected


def _item(workout_id, position, name, info="3x10", linked=False):
    return {
        "workout_id": workout_id,
        "position": position,
        "name": name,
        "info": info,
        "linked": linked,
    }


def test_normalize_sorts_groups_supersets_and_skips_rest_days():
    data = {
        "workouts": [
            {"id": 2, "due": "2026-10-13", "title": "Rest", "rest_day": True},
            {"id": 1, "due": "2026-10-12", "title": "Legs + Traps ", "rest_day": False},
        ],
        "workout_items": [
            _item(1, 3, "Dumbbell Shrug"),
            _item(1, 1, "Leg Extension ", linked=True),
            _item(1, 2, "Frog Pump", "4x15 pesado"),
        ],
        "comments": [],
    }
    [(due, routine)] = normalize(data)
    assert due == date(2026, 10, 12)
    assert (routine.day, routine.focus) == ("Monday", "Legs + Traps")
    assert routine.mobility == [] and routine.stretch == []
    assert [(e.group, e.name) for e in routine.exercises] == [
        ("A1", "Leg Extension"),
        ("A2", "Frog Pump"),
        ("B", "Dumbbell Shrug"),
    ]
    assert routine.exercises[1].extra == ["pesado"]


def test_linked_last_item_is_not_a_superset():
    data = {
        "workouts": [{"id": 1, "due": "2026-10-12", "title": "x", "rest_day": False}],
        "workout_items": [_item(1, 1, "A thing", linked=True)],
        "comments": [],
    }
    [(_, routine)] = normalize(data)
    assert routine.exercises[0].group == "A"
