import json
import re
from datetime import date
from pathlib import Path
from string import ascii_uppercase

from workout_coach.models import DayRoutine, Exercise

WEEKDAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

_SETS = r"\d+\s*x\s*\d+(?:-\d+)?(?:\s+(?:reps|por lado|segundos|seg)\b)*"
_HEAD = re.compile(rf"^({_SETS})\s*(.*)$", re.IGNORECASE)
_SETS_ONLY = re.compile(rf"^{_SETS}$", re.IGNORECASE)


def parse_info(info: str) -> tuple[str, list[str]]:
    """Split the trainer's free text into (sets_reps, extra).

    "3x20 reps\\npasos largos" -> ("3x20 reps", ["pasos largos"]). When the text
    does not start with a regular scheme, the raw text is kept as sets_reps.
    """
    lines = [line.strip() for line in info.splitlines() if line.strip()]
    if not lines:
        return "", []
    head = _HEAD.match(lines[0])
    if not head:
        return " ".join(lines), []
    sets_reps = [head.group(1)]
    extra = [head.group(2)] if head.group(2) else []
    for line in lines[1:]:
        if _SETS_ONLY.match(line):
            sets_reps.append(line)
        else:
            extra.append(line)
    return ", ".join(sets_reps), extra


def _blocks(items: list[dict]) -> list[list[dict]]:
    """Group items into blocks. An item with `linked` is superset with the next one."""
    blocks: list[list[dict]] = []
    joined = False
    for item in items:
        if joined:
            blocks[-1].append(item)
        else:
            blocks.append([item])
        joined = item["linked"]
    return blocks


def _exercises(items: list[dict]) -> list[Exercise]:
    blocks = _blocks(sorted(items, key=lambda item: item["position"]))
    if len(blocks) > len(ascii_uppercase):
        raise ValueError(f"{len(blocks)} blocks, only {len(ascii_uppercase)} letters")
    exercises = []
    for letter, block in zip(ascii_uppercase, blocks):
        for number, item in enumerate(block, start=1):
            sets_reps, extra = parse_info(item["info"])
            exercises.append(
                Exercise(
                    group=letter + (str(number) if len(block) > 1 else ""),
                    name=item["name"].strip(),
                    sets_reps=sets_reps,
                    extra=extra,
                )
            )
    return exercises


def normalize(data: dict) -> list[tuple[date, DayRoutine]]:
    """Map a raw snapshot to (due date, DayRoutine) pairs, oldest first.

    Mapping only: nothing is adjusted. Rest days are skipped. TrueCoach carries no
    mobility, stretch or reference file, so those stay empty.
    """
    items_by_workout: dict[int, list[dict]] = {}
    for item in data["workout_items"]:
        items_by_workout.setdefault(item["workout_id"], []).append(item)
    days = []
    for workout in sorted(data["workouts"], key=lambda w: w["due"]):
        if workout["rest_day"]:
            continue
        due = date.fromisoformat(workout["due"])
        routine = DayRoutine(
            day=WEEKDAYS[due.weekday()],
            focus=workout["title"].strip(),
            mobility=[],
            stretch=[],
            exercises=_exercises(items_by_workout.get(workout["id"], [])),
        )
        days.append((due, routine))
    return days


def load_snapshot(path: Path) -> dict:
    return json.loads(path.read_text())
