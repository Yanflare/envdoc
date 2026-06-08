"""Scan Python source files for environment variable access patterns."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

import libcst as cst
from libcst.metadata import MetadataWrapper, PositionProvider


@dataclass
class EnvVar:
    """A detected environment variable reference."""

    key: str
    default: str | None
    source_file: Path
    line_number: int


class _EnvVarVisitor(cst.CSTVisitor):
    """libcst visitor that collects env var references."""

    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, source_file: Path) -> None:
        self.source_file = source_file
        self.found: list[EnvVar] = []

    def _str_value(self, node: cst.BaseExpression) -> str | None:
        """Safely evaluate a string literal; return None for non-literals."""
        if isinstance(node, cst.SimpleString):
            try:
                val = ast.literal_eval(node.value)
                return val if isinstance(val, str) else None
            except (ValueError, SyntaxError):
                return None
        return None

    def _is_os_getenv(self, node: cst.Call) -> bool:
        return (
            isinstance(node.func, cst.Attribute)
            and isinstance(node.func.value, cst.Name)
            and node.func.value.value == "os"
            and node.func.attr.value == "getenv"
        )

    def _is_os_environ_get(self, node: cst.Call) -> bool:
        if not isinstance(node.func, cst.Attribute):
            return False
        if node.func.attr.value != "get":
            return False
        inner = node.func.value
        return (
            isinstance(inner, cst.Attribute)
            and isinstance(inner.value, cst.Name)
            and inner.value.value == "os"
            and inner.attr.value == "environ"
        )

    def _args_to_key_default(self, node: cst.Call) -> tuple[str | None, str | None]:
        """Extract (key, default) from the first two positional arguments."""
        args = node.args
        if not args:
            return None, None
        key = self._str_value(args[0].value)
        default = self._str_value(args[1].value) if len(args) >= 2 else None
        return key, default

    def _record(self, node: cst.CSTNode, key: str, default: str | None) -> None:
        pos = self.get_metadata(PositionProvider, node)
        self.found.append(
            EnvVar(
                key=key,
                default=default,
                source_file=self.source_file,
                line_number=pos.start.line,
            )
        )

    def visit_Call(self, node: cst.Call) -> bool | None:
        if self._is_os_getenv(node) or self._is_os_environ_get(node):
            key, default = self._args_to_key_default(node)
            if key is not None:
                self._record(node, key, default)
        return None

    def visit_Subscript(self, node: cst.Subscript) -> bool | None:
        """Detect os.environ['KEY'] subscript access."""
        if not (
            isinstance(node.value, cst.Attribute)
            and isinstance(node.value.value, cst.Name)
            and node.value.value.value == "os"
            and node.value.attr.value == "environ"
        ):
            return None
        if not node.slice:
            return None
        first = node.slice[0]
        if isinstance(first, cst.SubscriptElement) and isinstance(first.slice, cst.Index):
            key = self._str_value(first.slice.value)
            if key is not None:
                self._record(node, key, None)
        return None


def scan_file(path: Path) -> list[EnvVar]:
    """Parse one Python file and return all detected env var references."""
    try:
        source = path.read_text(encoding="utf-8")
        module = cst.parse_module(source)
        wrapper = MetadataWrapper(module)
        visitor = _EnvVarVisitor(path)
        wrapper.visit(visitor)
        return visitor.found
    except Exception:  # skip files with parse or encoding errors
        return []


def scan_path(path: Path, ignored: set[Path]) -> list[EnvVar]:
    """Recursively scan *path* for env var usage, skipping *ignored* paths."""
    results: list[EnvVar] = []
    if path.is_file():
        if path.suffix == ".py" and path.resolve() not in ignored:
            results.extend(scan_file(path))
    else:
        for py_file in sorted(path.rglob("*.py")):
            if py_file.resolve() not in ignored:
                results.extend(scan_file(py_file))
    return results
