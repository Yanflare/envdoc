"""Tests for envdoc.generator module."""

from __future__ import annotations

from pathlib import Path

from envdoc.generator import check_stale, render_dotenv, render_markdown
from envdoc.scanner import EnvVar


def _var(key: str, default: str | None = None, line: int = 1) -> EnvVar:
    return EnvVar(key=key, default=default, source_file=Path("app.py"), line_number=line)


def test_dotenv_format_no_default() -> None:
    assert "SECRET_KEY=" in render_dotenv([_var("SECRET_KEY")])


def test_dotenv_format_with_default() -> None:
    assert "PORT=8000" in render_dotenv([_var("PORT", "8000")])


def test_dotenv_includes_source_comment() -> None:
    assert "# source: app.py:42" in render_dotenv([_var("FOO", line=42)])


def test_dotenv_multiple_vars() -> None:
    result = render_dotenv([_var("A"), _var("B", "val")])
    assert "A=" in result
    assert "B=val" in result


def test_dotenv_empty_returns_empty_string() -> None:
    assert render_dotenv([]) == ""


def test_markdown_table_row() -> None:
    assert "| `DB_URL` |" in render_markdown([_var("DB_URL")])


def test_markdown_header_present() -> None:
    assert "# Environment Variables" in render_markdown([_var("X")])


def test_markdown_table_header_columns() -> None:
    result = render_markdown([_var("X")])
    assert "| Key |" in result
    assert "| Default |" in result
    assert "| Source |" in result


def test_markdown_empty_vars() -> None:
    assert "No environment variables detected." in render_markdown([])


def test_check_stale_true_when_missing(tmp_path: Path) -> None:
    assert check_stale(tmp_path / ".env.example", "KEY=\n") is True


def test_check_stale_true_when_different(tmp_path: Path) -> None:
    f = tmp_path / ".env.example"
    f.write_text("OLD_KEY=\n")
    assert check_stale(f, "NEW_KEY=\n") is True


def test_check_stale_false_when_same(tmp_path: Path) -> None:
    f = tmp_path / ".env.example"
    f.write_text("KEY=\n")
    assert check_stale(f, "KEY=\n") is False
