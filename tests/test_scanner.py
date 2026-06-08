"""Tests for envdoc.scanner module."""

from __future__ import annotations

from pathlib import Path

from envdoc.scanner import scan_file, scan_path

FIXTURES = Path(__file__).parent / "fixtures"


def test_detects_os_getenv() -> None:
    results = scan_file(FIXTURES / "basic.py")
    assert any(v.key == "DB_HOST" for v in results)


def test_detects_os_getenv_with_default() -> None:
    results = scan_file(FIXTURES / "basic.py")
    var = next(v for v in results if v.key == "DB_PORT")
    assert var.default == "5432"


def test_detects_os_environ_getitem() -> None:
    results = scan_file(FIXTURES / "basic.py")
    assert any(v.key == "SECRET_KEY" for v in results)


def test_detects_os_environ_get() -> None:
    results = scan_file(FIXTURES / "basic.py")
    assert any(v.key == "API_KEY" for v in results)


def test_detects_os_environ_get_with_default() -> None:
    results = scan_file(FIXTURES / "basic.py")
    var = next(v for v in results if v.key == "TIMEOUT")
    assert var.default == "30"


def test_returns_correct_line_numbers() -> None:
    results = scan_file(FIXTURES / "basic.py")
    var = next(v for v in results if v.key == "DB_HOST")
    assert var.line_number > 0


def test_skips_non_python_files(tmp_path: Path) -> None:
    (tmp_path / "config.txt").write_text('os.getenv("SHOULD_NOT_DETECT")\n')
    results = scan_path(tmp_path, set())
    assert not any(v.key == "SHOULD_NOT_DETECT" for v in results)


def test_scan_path_returns_results_from_all_files() -> None:
    results = scan_path(FIXTURES, set())
    keys = [v.key for v in results]
    assert "DB_HOST" in keys
    assert "REDIS_HOST" in keys


def test_scan_path_respects_ignored(tmp_path: Path) -> None:
    py_file = tmp_path / "secret.py"
    py_file.write_text('import os\nX = os.getenv("IGNORED_KEY")\n')
    results = scan_path(tmp_path, {py_file.resolve()})
    assert not any(v.key == "IGNORED_KEY" for v in results)


def test_no_envvars_file_returns_empty() -> None:
    assert scan_file(FIXTURES / "no_envvars.py") == []
