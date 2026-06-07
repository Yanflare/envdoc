"""Smoke tests — verify CLI entry point loads cleanly."""

from typer.testing import CliRunner
from envdoc.cli import app

runner = CliRunner()


def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "envdoc" in result.output


def test_scan_stub():
    result = runner.invoke(app, ["scan", "."])
    assert result.exit_code == 0
