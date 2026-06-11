"""Tests for python-dotenv usage detection (_DotenvVisitor)."""
from __future__ import annotations

import textwrap
from pathlib import Path

from envdoc.scanner import scan_file

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _scan(src: str, tmp_path: Path) -> list[str]:
    """Write *src* to a temp file, scan it, return list of detected keys."""
    f = tmp_path / "sample.py"
    f.write_text(textwrap.dedent(src))
    results = scan_file(f)
    return [r.key for r in results]


# ---------------------------------------------------------------------------
# Basic import styles
# ---------------------------------------------------------------------------

def test_load_dotenv_bare(tmp_path: Path) -> None:
    """Bare load_dotenv() with no path → generic dotenv note."""
    src = """\
        from dotenv import load_dotenv
        load_dotenv()
    """
    keys = _scan(src, tmp_path)
    assert "# dotenv:.env" in keys


def test_load_dotenv_positional_path(tmp_path: Path) -> None:
    """load_dotenv('.env.production') → path captured in key."""
    src = """\
        from dotenv import load_dotenv
        load_dotenv(".env.production")
    """
    keys = _scan(src, tmp_path)
    assert "# dotenv:.env.production" in keys


def test_load_dotenv_keyword_path(tmp_path: Path) -> None:
    """load_dotenv(dotenv_path='.env.staging') → path captured in key."""
    src = """\
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=".env.staging")
    """
    keys = _scan(src, tmp_path)
    assert "# dotenv:.env.staging" in keys


def test_dotenv_values_positional(tmp_path: Path) -> None:
    """dotenv_values('.env') → path captured."""
    src = """\
        from dotenv import dotenv_values
        config = dotenv_values(".env")
    """
    keys = _scan(src, tmp_path)
    assert "# dotenv:.env" in keys


# ---------------------------------------------------------------------------
# Aliased imports
# ---------------------------------------------------------------------------

def test_load_dotenv_aliased(tmp_path: Path) -> None:
    """from dotenv import load_dotenv as ld → alias resolved."""
    src = """\
        from dotenv import load_dotenv as ld
        ld(".env.test")
    """
    keys = _scan(src, tmp_path)
    assert "# dotenv:.env.test" in keys


def test_dotenv_values_aliased(tmp_path: Path) -> None:
    """from dotenv import dotenv_values as dv → alias resolved."""
    src = """\
        from dotenv import dotenv_values as dv
        cfg = dv(".env.local")
    """
    keys = _scan(src, tmp_path)
    assert "# dotenv:.env.local" in keys


# ---------------------------------------------------------------------------
# Namespace import style
# ---------------------------------------------------------------------------

def test_import_dotenv_namespace(tmp_path: Path) -> None:
    """import dotenv; dotenv.load_dotenv(...) → detected."""
    src = """\
        import dotenv
        dotenv.load_dotenv(dotenv_path=".env.prod")
    """
    keys = _scan(src, tmp_path)
    assert "# dotenv:.env.prod" in keys


def test_import_dotenv_namespace_bare(tmp_path: Path) -> None:
    """import dotenv; dotenv.load_dotenv() with no path → generic note."""
    src = """\
        import dotenv
        dotenv.load_dotenv()
    """
    keys = _scan(src, tmp_path)
    assert "# dotenv:.env" in keys


# ---------------------------------------------------------------------------
# Co-existence with existing visitors
# ---------------------------------------------------------------------------

def test_dotenv_plus_os_getenv(tmp_path: Path) -> None:
    """dotenv + os.getenv in the same file → both detected."""
    src = """\
        import os
        from dotenv import load_dotenv
        load_dotenv()
        SECRET = os.getenv("SECRET_KEY")
    """
    keys = _scan(src, tmp_path)
    assert "# dotenv:.env" in keys
    assert "SECRET_KEY" in keys


# ---------------------------------------------------------------------------
# Negative cases — no false positives
# ---------------------------------------------------------------------------

def test_unrelated_call_not_detected(tmp_path: Path) -> None:
    """Calls that look similar but are not dotenv should not be detected."""
    src = """\
        def load_dotenv(path):
            pass
        load_dotenv(".env")
    """
    keys = _scan(src, tmp_path)
    # No import from dotenv → visitor should be silent
    assert not any(k.startswith("# dotenv:") for k in keys)


def test_no_dotenv_import_no_detection(tmp_path: Path) -> None:
    """A file with no dotenv import produces no dotenv keys."""
    src = """\
        import os
        VAL = os.getenv("NORMAL_VAR")
    """
    keys = _scan(src, tmp_path)
    assert not any(k.startswith("# dotenv:") for k in keys)
    assert "NORMAL_VAR" in keys
