import typer
from anthropic import Anthropic
from dotenv import load_dotenv
from rich.console import Console

MODEL = "claude-haiku-5-5"

app = typer.Typer(
    help="Review TrueCoach workouts against an injury history.", no_args_is_help=True
)
console = Console()


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
