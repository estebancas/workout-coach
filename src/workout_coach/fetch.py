import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from workout_coach.truecoach import TrueCoachClient

SNAPSHOT_DIR = Path("data/snapshots")
PER_PAGE = 50


def next_full_week(today: date) -> tuple[date, date]:
    """The Monday-to-Sunday week after the current one."""
    monday = today - timedelta(days=today.weekday()) + timedelta(days=7)
    return monday, monday + timedelta(days=6)


def fetch_workouts(
    client: TrueCoachClient, start: date, end: date, states: str = "pending"
) -> dict:
    """Fetch every page, keep workouts due in [start, end], return the raw shape."""
    client_id = client.me()["clients"][0]["id"]
    workouts, items, comments = [], [], []
    page = 1
    while True:
        data = client.request(
            "GET",
            f"/clients/{client_id}/workouts",
            params={
                "order": "asc",
                "page": page,
                "per_page": PER_PAGE,
                "states": states,
            },
        ).json()
        workouts += data["workouts"]
        items += data["workout_items"]
        comments += data["comments"]
        if page >= data["meta"]["total_pages"]:
            break
        page += 1
    kept = [w for w in workouts if start.isoformat() <= w["due"] <= end.isoformat()]
    ids = {w["id"] for w in kept}
    return {
        "workouts": kept,
        "workout_items": [i for i in items if i["workout_id"] in ids],
        "comments": [c for c in comments if c.get("workout_id") in ids],
    }


def save_snapshot(
    data: dict, start: date, end: date, directory: Path = SNAPSHOT_DIR
) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = directory / f"{start}_{end}_{stamp}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    return path


def summarize(data: dict) -> list[tuple[str, str, int]]:
    counts: dict[int, int] = {}
    for item in data["workout_items"]:
        counts[item["workout_id"]] = counts.get(item["workout_id"], 0) + 1
    return [(w["due"], w["title"], counts.get(w["id"], 0)) for w in data["workouts"]]
