from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Weekday = Literal[
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Item(Strict):
    """A mobility (warm-up) or stretch (night) entry."""

    name: str
    description: str
    sets_reps: str
    extra: list[str] = []


class Exercise(Strict):
    """A gym exercise. Groups like D1/D2 are supersets, in order."""

    group: str = Field(pattern=r"^[A-Z]+\d*$")
    name: str
    sets_reps: str
    extra: list[str] = []


class DayRoutine(Strict):
    day: Weekday
    focus: str
    reference_file: str | None = None
    mobility: list[Item]
    stretch: list[Item]
    exercises: list[Exercise]


class Routine(Strict):
    weekly_routine: list[DayRoutine]


class Adjustment(Strict):
    """A change the AI made to an exercise. Shown in review, never written to routine.json."""

    exercise: str
    change: str
    reason: str
    injury: str = Field(
        description="The injury area from the athlete profile this protects."
    )


def json_schemas() -> dict[str, dict]:
    """JSON Schemas to use as tool definitions later."""
    return {
        "DayRoutine": DayRoutine.model_json_schema(),
        "Adjustment": Adjustment.model_json_schema(),
    }
