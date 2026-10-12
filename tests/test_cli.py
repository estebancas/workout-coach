from types import SimpleNamespace

from typer.testing import CliRunner

from workout_coach import cli

runner = CliRunner()


def test_ping_prints_reply_and_usage(monkeypatch):
    message = SimpleNamespace(
        model="test-model",
        content=[SimpleNamespace(type="text", text="pong")],
        usage=SimpleNamespace(input_tokens=7, output_tokens=2),
    )

    class FakeClient:
        messages = SimpleNamespace(create=lambda **_: message)

    monkeypatch.setattr(cli, "Anthropic", FakeClient)
    result = runner.invoke(cli.app, ["ping"])
    assert result.exit_code == 0
    assert "pong" in result.output
    assert "input_tokens=7" in result.output
    assert "output_tokens=2" in result.output


def test_normalize_prints_one_row_per_day(tmp_path):
    snapshot = tmp_path / "week.json"
    snapshot.write_text(
        '{"workouts": [{"id": 1, "due": "2026-10-12", "title": "Legs", '
        '"rest_day": false}], "workout_items": [{"workout_id": 1, "position": 1, '
        '"name": "Back Squat", "info": "3x10", "linked": false}], "comments": []}'
    )
    result = runner.invoke(cli.app, ["normalize", str(snapshot)])
    assert result.exit_code == 0
    assert "Monday" in result.output and "Legs" in result.output
