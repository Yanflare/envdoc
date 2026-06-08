"""Find and apply .gitignore patterns to filter scan paths."""

from __future__ import annotations

from pathlib import Path

import pathspec


def find_gitignore(start: Path) -> Path | None:
    """Walk up from *start* to find the nearest .gitignore file."""
    current = start.resolve()
    while True:
        candidate = current / ".gitignore"
        if candidate.is_file():
            return candidate
        parent = current.parent
        if parent == current:
            return None
        current = parent


def load_ignored(root: Path) -> set[Path]:
    """Return absolute Paths under *root* that match .gitignore patterns."""
    gitignore_path = find_gitignore(root)
    if gitignore_path is None:
        return set()

    lines = gitignore_path.read_text(encoding="utf-8").splitlines()
    spec = pathspec.PathSpec.from_lines("gitignore", lines)

    root_resolved = root.resolve()
    ignored: set[Path] = set()

    for candidate in root_resolved.rglob("*"):
        try:
            rel = str(candidate.relative_to(root_resolved))
            if spec.match_file(rel):
                ignored.add(candidate.resolve())
        except ValueError:
            pass

    return ignored
