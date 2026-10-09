from enum import StrEnum
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel

DEFAULT_PATH = Path("profile/athlete.yaml")


class Status(StrEnum):
    ACUTE = "acute"
    RECOVERING = "recovering"
    MAINTENANCE = "maintenance"


class Injury(BaseModel):
    area: str
    side: Literal["left", "right", "both"]
    diagnosis: str
    since: str | None = None
    status: Status
    avoid: list[str] = []
    modify: list[str] = []
    prefer: list[str] = []
    notes: str | None = None


class Context(BaseModel):
    occupation: str
    goals: list[str]
    equipment: str
    care_team: list[str] = []


class Policy(BaseModel):
    conflicts: Literal["substitute", "modify", "flag"]
    on_pain: Literal["stop_and_substitute", "reduce_and_continue", "pain_scale"]
    warmup_minutes: int | None = None
    stretch_minutes: int | None = None


class AthleteProfile(BaseModel):
    language: str
    context: Context
    policy: Policy
    injuries: list[Injury]


def load_profile(path: Path = DEFAULT_PATH) -> AthleteProfile:
    return AthleteProfile.model_validate(yaml.safe_load(path.read_text()))
