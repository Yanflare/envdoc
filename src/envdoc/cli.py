"""envdoc CLI entry point."""
from __future__ import annotations

import typer
from rich.console import Console

app = typer.Typer(
    name="envdoc",
    help="Scan a Python codebase for env var usage and generate .env.example / Markdown docs.",
    add_completion=False,
)

console = Console()
@app.callback()
def callback() -> None:
    """envdoc — auto-document your environment variables."""
@app.command()
def scan(
    path: str = typer.Argument(".", help="Path to scan (file or directory)."),
    output_format: str = typer.Option(
        "dotenv", "--format", "-f", help="Output format: dotenv | markdown"
    ),
    check: bool = typer.Option(
        False, "--check", help="Exit non-zero if .env.example is stale."
    ),
    output: str | None = typer.Option(
        None, "--output", "-o", help="Write output to file instead of stdout."
    ),
) -> None:
    """Scan PATH for environment variable usage and generate documentation."""
    console.print(f"[bold cyan]envdoc[/] scanning [green]{path}[/] …")
    console.print("[yellow]⚠[/]  Core scanner not yet implemented — coming in v0.1.0.")
    raise typer.Exit(code=0)
if __name__ == "__main__":
    app()
