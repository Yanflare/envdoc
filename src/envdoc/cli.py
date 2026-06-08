"""envdoc CLI entry point."""

from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich.console import Console

from envdoc import generator, gitignore, scanner

app = typer.Typer(
    name="envdoc",
    help="Scan a Python codebase for env var usage and generate .env.example / Markdown docs.",
    add_completion=False,
)
console = Console()
err_console = Console(stderr=True)


@app.callback()
def callback() -> None:
    """envdoc — auto-document your environment variables."""


@app.command()
def scan(
    path: str = typer.Argument(".", help="Path to scan (file or directory)."),
    output_format: str = typer.Option(
        "dotenv", "--format", "-f", help="Output format: dotenv | markdown"
    ),
    check: bool = typer.Option(False, "--check", help="Exit non-zero if .env.example is stale."),
    output: str | None = typer.Option(
        None, "--output", "-o", help="Write output to file instead of stdout."
    ),
) -> None:
    """Scan PATH for environment variable usage and generate documentation."""
    scan_target = Path(path).resolve()

    if not scan_target.exists():
        err_console.print(f"[red]Error:[/] path does not exist: {path}")
        raise typer.Exit(code=1)

    ignored = gitignore.load_ignored(scan_target if scan_target.is_dir() else scan_target.parent)
    env_vars = scanner.scan_path(scan_target, ignored)

    # Deduplicate: keep first occurrence of each key
    seen: set[str] = set()
    unique: list[scanner.EnvVar] = []
    for var in env_vars:
        if var.key not in seen:
            seen.add(var.key)
            unique.append(var)

    rendered = (
        generator.render_markdown(unique)
        if output_format == "markdown"
        else generator.render_dotenv(unique)
    )

    if check:
        check_file = Path(output) if output else Path(".env.example")
        if generator.check_stale(check_file, rendered):
            err_console.print(
                f"[red]✗[/] {check_file} is stale or missing — run `envdoc scan` to regenerate."
            )
            raise typer.Exit(code=1)
        console.print(f"[green]✓[/] {check_file} is up to date.")
        raise typer.Exit(code=0)

    if output:
        out_path = Path(output)
        out_path.write_text(rendered, encoding="utf-8")
        console.print(
            f"[bold cyan]envdoc[/] found [bold]{len(unique)}[/] env var(s) — "
            f"written to [green]{out_path}[/]"
        )
    else:
        sys.stdout.write(rendered)


if __name__ == "__main__":
    app()
