"""Smoke tests — verify CLI entry point loads cleanly."""
from typer.testing import CliRunner

from envdoc.cli import app

runner = CliRunner()


def test_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "scan" in result.output


def test_scan_stub() -> None:
    result = runner.invoke(app, ["scan", "."])
    assert result.exit_code == 0
