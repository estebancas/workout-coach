from datetime import date, datetime
from pathlib import Path
from typing import Annotated

import typer
from anthropic import Anthropic
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from workout_coach.fetch import (
    SNAPSHOT_DIR,
    fetch_workouts,
    next_full_week,
    save_snapshot,
    summarize,
)
from workout_coach.normalize import load_snapshot, normalize
from workout_coach.truecoach import AuthError, TrueCoachClient, save_credentials

MODEL = "claude-haiku-5-5"

app = typer.Typer(
    help="Review TrueCoach workouts against an injury history.", no_args_is_help=True
)
console = Console()
auth_app = typer.Typer(help="Manage TrueCoach credentials.", no_args_is_help=True)
app.add_typer(auth_app, name="auth")


@app.callback()
def _root() -> None:
    load_dotenv()


@app.command()
def ping(
    prompt: str = "Reply with one short sentence confirming you are reachable.",
) -> None:
    """Make one Messages API call and print the reply and token usage."""
    client = Anthropic()
    message = client.messages.create(
        model=MODEL,
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}],
    )
    reply = "".join(block.text for block in message.content if block.type == "text")
    console.print(reply)
    console.print(
        f"[dim]model={message.model} input_tokens={message.usage.input_tokens} "
        f"output_tokens={message.usage.output_tokens}[/dim]"
    )


@auth_app.command("set")
def auth_set() -> None:
    """Store the TrueCoach email and password in the OS keychain."""
    email = typer.prompt("TrueCoach email")
    password = typer.prompt("TrueCoach password", hide_input=True)
    save_credentials(email, password)
    console.print("Credentials saved to the keychain.")


@app.command()
def whoami() -> None:
    """Print the TrueCoach client id and name."""
    client = TrueCoachClient()
    try:
        data = client.me()
    except AuthError as error:
        console.print(f"[red]{error}[/red]")
        raise typer.Exit(1) from error
    user = data["user"]
    name = " ".join(filter(None, [user.get("first_name"), user.get("last_name")]))
    console.print(f"client_id={data['clients'][0]['id']} name={name or '(unknown)'}")


@app.command()
def fetch(
    start: str = typer.Option(
        None, "--from", help="First day, YYYY-MM-DD. Default: next Monday."
    ),
    end: str = typer.Option(
        None, "--to", help="Last day, YYYY-MM-DD. Default: next Sunday."
    ),
    states: str = typer.Option("pending", help="TrueCoach workout states to include."),
) -> None:
    """Fetch workouts for a date range, save a raw snapshot, print a summary."""
    default_start, default_end = next_full_week(datetime.now().astimezone().date())
    first = date.fromisoformat(start) if start else default_start
    last = date.fromisoformat(end) if end else default_end
    try:
        data = fetch_workouts(TrueCoachClient(), first, last, states)
    except AuthError as error:
        console.print(f"[red]{error}[/red]")
        raise typer.Exit(1) from error
    if not data["workouts"]:
        console.print(f"No workouts between {first} and {last} (states={states}).")
        raise typer.Exit(1)
    path = save_snapshot(data, first, last)
    table = Table("Date", "Title", "Exercises")
    for due, title, count in summarize(data):
        table.add_row(due, title, str(count))
    console.print(table)
    console.print(f"[dim]Saved {path}[/dim]")


@app.command("normalize")
def normalize_command(
    paths: Annotated[
        list[Path] | None,
        typer.Argument(help="Snapshot files. Default: every file in data/snapshots."),
    ] = None,
) -> None:
    """Map raw snapshots to DayRoutine objects (no LLM) and print a summary."""
    files = paths or sorted(SNAPSHOT_DIR.glob("*.json"))
    if not files:
        console.print("No snapshots found. Run `workout-coach fetch` first.")
        raise typer.Exit(1)
    table = Table("Date", "Day", "Focus", "Exercises")
    for file in files:
        for due, routine in normalize(load_snapshot(file)):
            table.add_row(
                due.isoformat(), routine.day, routine.focus, str(len(routine.exercises))
            )
    console.print(table)
