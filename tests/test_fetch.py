from datetime import date

import httpx

from workout_coach.fetch import fetch_workouts, next_full_week, summarize
from workout_coach.truecoach import TrueCoachClient


def test_next_full_week_from_midweek_and_monday():
    assert next_full_week(date(2026, 10, 8)) == (date(2026, 10, 12), date(2026, 10, 18))
    assert next_full_week(date(2026, 10, 12)) == (
        date(2026, 10, 19),
        date(2026, 10, 25),
    )


def test_fetch_paginates_and_filters_by_due(tmp_path):
    (tmp_path / "token.json").write_text('{"access_token": "t"}')
    pages = {
        1: {
            "workouts": [{"id": 1, "due": "2026-10-09", "title": "Out"}],
            "workout_items": [{"workout_id": 1, "position": 0}],
            "comments": [],
            "meta": {"total_pages": 2},
        },
        2: {
            "workouts": [{"id": 2, "due": "2026-10-12", "title": "In"}],
            "workout_items": [
                {"workout_id": 2, "position": 1},
                {"workout_id": 2, "position": 0},
            ],
            "comments": [],
            "meta": {"total_pages": 2},
        },
    }

    def handler(request):
        if request.url.path.endswith("/users/me"):
            return httpx.Response(200, json={"clients": [{"id": 5}]})
        return httpx.Response(200, json=pages[int(request.url.params["page"])])

    client = TrueCoachClient(
        transport=httpx.MockTransport(handler), token_cache=tmp_path / "token.json"
    )
    data = fetch_workouts(client, date(2026, 10, 12), date(2026, 10, 18))
    assert [w["id"] for w in data["workouts"]] == [2]
    assert len(data["workout_items"]) == 2
    assert summarize(data) == [("2026-10-12", "In", 2)]
