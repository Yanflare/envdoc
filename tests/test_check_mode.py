"""Tests for envdoc CLI --check mode."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from envdoc.cli import app

runner = CliRunner()


def test_check_exits_0_when_current(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text('import os\nX = os.getenv("MY_KEY")\n')
    env_example = tmp_path / ".env.example"

    r = runner.invoke(app, ["scan", str(tmp_path), "--output", str(env_example)])
    assert r.exit_code == 0

    r2 = runner.invoke(app, ["scan", str(tmp_path), "--check", "--output", str(env_example)])
    assert r2.exit_code == 0


def test_check_exits_1_when_stale(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text('import os\nX = os.getenv("MY_KEY")\n')
    env_example = tmp_path / ".env.example"
    env_example.write_text("STALE_KEY=\n")

    r = runner.invoke(app, ["scan", str(tmp_path), "--check", "--output", str(env_example)])
    assert r.exit_code == 1


def test_check_exits_1_when_missing(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text('import os\nX = os.getenv("MY_KEY")\n')
    env_example = tmp_path / ".env.example"

    r = runner.invoke(app, ["scan", str(tmp_path), "--check", "--output", str(env_example)])
    assert r.exit_code == 1
