"""Generate .env.example and Markdown docs from detected env vars."""

from __future__ import annotations

from pathlib import Path

from envdoc.scanner import EnvVar


def render_dotenv(env_vars: list[EnvVar]) -> str:
    """Render .env.example content from detected env vars."""
    if not env_vars:
        return ""
    lines: list[str] = []
    for var in env_vars:
        lines.append(f"# source: {var.source_file}:{var.line_number}")
        value = var.default if var.default is not None else ""
        lines.append(f"{var.key}={value}")
    return "\n".join(lines) + "\n"


def render_markdown(env_vars: list[EnvVar]) -> str:
    """Render a Markdown config-reference table from detected env vars."""
    if not env_vars:
        return "No environment variables detected.\n"
    lines = [
        "# Environment Variables",
        "",
        "| Key | Default | Source |",
        "|-----|---------|--------|",
    ]
    for var in env_vars:
        default = var.default if var.default is not None else ""
        source = f"{var.source_file}:{var.line_number}"
        lines.append(f"| `{var.key}` | `{default}` | {source} |")
    return "\n".join(lines) + "\n"


def check_stale(current_file: Path, fresh: str) -> bool:
    """Return True if *current_file* is missing or its content differs from *fresh*."""
    if not current_file.exists():
        return True
    return current_file.read_text(encoding="utf-8") != fresh
