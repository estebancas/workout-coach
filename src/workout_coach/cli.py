import typer
from anthropic import Anthropic
from dotenv import load_dotenv
from rich.console import Console

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
