"""Tests for Pydantic BaseSettings env var detection."""
from __future__ import annotations

import textwrap
from pathlib import Path

from envdoc.scanner import scan_file


def _write(tmp_path: Path, source: str) -> Path:
    p = tmp_path / "settings.py"
    p.write_text(textwrap.dedent(source))
    return p


# ---------------------------------------------------------------------------
# Basic detection
# ---------------------------------------------------------------------------


def test_basic_pydantic_settings(tmp_path: Path) -> None:
    """Detects fields on a class that inherits from BaseSettings."""
    p = _write(
        tmp_path,
        """\
        from pydantic_settings import BaseSettings

        class Config(BaseSettings):
            DATABASE_URL: str
            SECRET_KEY: str
            PORT: int
        """,
    )
    results = scan_file(p)
    keys = [r.key for r in results]
    assert "DATABASE_URL" in keys
    assert "SECRET_KEY" in keys
    assert "PORT" in keys


def test_default_value_string(tmp_path: Path) -> None:
    """String literal defaults are captured."""
    p = _write(
        tmp_path,
        """\
        from pydantic_settings import BaseSettings

        class Config(BaseSettings):
            LOG_LEVEL: str = "INFO"
        """,
    )
    results = scan_file(p)
    assert len(results) == 1
    assert results[0].key == "LOG_LEVEL"
    assert results[0].default == "INFO"


def test_default_value_integer(tmp_path: Path) -> None:
    """Integer literal defaults are captured as strings."""
    p = _write(
        tmp_path,
        """\
        from pydantic_settings import BaseSettings

        class Config(BaseSettings):
            PORT: int = 8080
        """,
    )
    results = scan_file(p)
    assert results[0].default == "8080"


def test_default_value_bool(tmp_path: Path) -> None:
    """Boolean literal defaults are captured."""
    p = _write(
        tmp_path,
        """\
        from pydantic_settings import BaseSettings

        class Config(BaseSettings):
            DEBUG: bool = False
        """,
    )
    results = scan_file(p)
    assert results[0].default == "False"


def test_no_default(tmp_path: Path) -> None:
    """Fields without defaults have default=None."""
    p = _write(
        tmp_path,
        """\
        from pydantic_settings import BaseSettings

        class Config(BaseSettings):
            API_KEY: str
        """,
    )
    results = scan_file(p)
    assert results[0].default is None


# ---------------------------------------------------------------------------
# Import style variants
# ---------------------------------------------------------------------------


def test_pydantic_v1_compat_import(tmp_path: Path) -> None:
    """Handles: from pydantic import BaseSettings (v1 compat path)."""
    p = _write(
        tmp_path,
        """\
        from pydantic import BaseSettings

        class Config(BaseSettings):
            DB_HOST: str
        """,
    )
    results = scan_file(p)
    assert any(r.key == "DB_HOST" for r in results)


def test_aliased_import(tmp_path: Path) -> None:
    """Handles: from pydantic_settings import BaseSettings as BS."""
    p = _write(
        tmp_path,
        """\
        from pydantic_settings import BaseSettings as BS

        class Config(BS):
            REDIS_URL: str
        """,
    )
    results = scan_file(p)
    assert any(r.key == "REDIS_URL" for r in results)


# ---------------------------------------------------------------------------
# Edge cases — should NOT be detected
# ---------------------------------------------------------------------------


def test_private_fields_skipped(tmp_path: Path) -> None:
    """Fields starting with _ are skipped."""
    p = _write(
        tmp_path,
        """\
        from pydantic_settings import BaseSettings

        class Config(BaseSettings):
            _internal: str = "x"
            PUBLIC_KEY: str
        """,
    )
    results = scan_file(p)
    keys = [r.key for r in results]
    assert "_internal" not in keys
    assert "PUBLIC_KEY" in keys


def test_model_config_skipped(tmp_path: Path) -> None:
    """model_config (pydantic v2 SettingsConfigDict) is skipped."""
    p = _write(
        tmp_path,
        """\
        from pydantic_settings import BaseSettings, SettingsConfigDict

        class Config(BaseSettings):
            model_config = SettingsConfigDict(env_prefix="APP_")
            API_KEY: str
        """,
    )
    results = scan_file(p)
    keys = [r.key for r in results]
    assert "model_config" not in keys
    assert "API_KEY" in keys


def test_non_settings_class_ignored(tmp_path: Path) -> None:
    """Regular classes are not scanned for settings fields."""
    p = _write(
        tmp_path,
        """\
        class NotSettings:
            DATABASE_URL: str
        """,
    )
    results = scan_file(p)
    assert results == []


def test_line_number_recorded(tmp_path: Path) -> None:
    """Line numbers are accurate for settings fields."""
    p = _write(
        tmp_path,
        """\
        from pydantic_settings import BaseSettings

        class Config(BaseSettings):
            FIRST: str
            SECOND: str
        """,
    )
    results = scan_file(p)
    by_key = {r.key: r for r in results}
    assert by_key["SECOND"].line_number > by_key["FIRST"].line_number


# ---------------------------------------------------------------------------
# Mixed: BaseSettings + os.getenv in the same file
# ---------------------------------------------------------------------------


def test_mixed_detection(tmp_path: Path) -> None:
    """BaseSettings fields and os.getenv calls are both detected."""
    p = _write(
        tmp_path,
        """\
        import os
        from pydantic_settings import BaseSettings

        LEGACY = os.getenv("LEGACY_KEY")

        class Config(BaseSettings):
            NEW_KEY: str
        """,
    )
    results = scan_file(p)
    keys = [r.key for r in results]
    assert "LEGACY_KEY" in keys
    assert "NEW_KEY" in keys
