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


# ---------------------------------------------------------------------------
# Pydantic BaseSettings detection
# ---------------------------------------------------------------------------

_SETTINGS_BASES = frozenset({"BaseSettings"})
_SETTINGS_MODULES = frozenset({"pydantic_settings", "pydantic"})


class _PydanticSettingsVisitor(cst.CSTVisitor):
    """Detect env vars declared as annotated attributes on BaseSettings subclasses.

    Handles both import styles:
        from pydantic_settings import BaseSettings
        from pydantic import BaseSettings          # v1 compat
        import pydantic_settings as ps; class C(ps.BaseSettings): ...  (best-effort)
    """

    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, source_file: Path) -> None:
        self.source_file = source_file
        self.found: list[EnvVar] = []
        # local names that resolve to BaseSettings (from import statements)
        self._settings_names: set[str] = set()
        # track whether we're inside a settings class and its body
        self._in_settings_class: bool = False

    # ------------------------------------------------------------------
    # Import tracking
    # ------------------------------------------------------------------

    def visit_ImportFrom(self, node: cst.ImportFrom) -> bool | None:
        """Track: from pydantic_settings import BaseSettings [as Alias]"""
        if not isinstance(node.names, (list, tuple)):
            return None
        # resolve module name — handles Name ("pydantic_settings") and
        # Attribute chains ("pydantic.something")
        if node.module is None:
            return None
        m = node.module
        if isinstance(m, cst.Name):
            module_name = m.value
        elif isinstance(m, cst.Attribute):
            # e.g. pydantic.v1 -> walk the chain
            parts: list[str] = []
            node_m: cst.BaseExpression = m
            while isinstance(node_m, cst.Attribute):
                parts.append(node_m.attr.value)
                node_m = node_m.value
            if isinstance(node_m, cst.Name):
                parts.append(node_m.value)
            module_name = ".".join(reversed(parts))
        else:
            return None

        # Accept pydantic_settings or pydantic (v1 compat path)
        if module_name not in _SETTINGS_MODULES:
            return None

        for alias in node.names:
            if not isinstance(alias, cst.ImportAlias):
                continue
            imported_name = (
                alias.name.value
                if isinstance(alias.name, cst.Name)
                else None
            )
            if imported_name not in _SETTINGS_BASES:
                continue
            local_name = imported_name
            if (
                alias.asname is not None
                and isinstance(alias.asname, cst.AsName)
                and isinstance(alias.asname.name, cst.Name)
            ):
                local_name = alias.asname.name.value
            self._settings_names.add(local_name)
        return None

    # ------------------------------------------------------------------
    # Class detection
    # ------------------------------------------------------------------

    def _class_inherits_settings(self, node: cst.ClassDef) -> bool:
        for arg in node.bases:
            base = arg.value
            # Direct name: class Config(BaseSettings)
            if isinstance(base, cst.Name) and base.value in self._settings_names:
                return True
            # Attribute: class Config(pydantic_settings.BaseSettings)
            if (
                isinstance(base, cst.Attribute)
                and isinstance(base.value, cst.Name)
                and base.attr.value in _SETTINGS_BASES
            ):
                return True
        return False

    def visit_ClassDef(self, node: cst.ClassDef) -> bool | None:
        if self._class_inherits_settings(node):
            self._in_settings_class = True
        return None

    def leave_ClassDef(self, original_node: cst.ClassDef) -> None:
        if self._in_settings_class and self._class_inherits_settings(original_node):
            self._in_settings_class = False

    # ------------------------------------------------------------------
    # Attribute collection
    # ------------------------------------------------------------------

    def _simple_default(self, annotation_node: cst.BaseExpression) -> str | None:
        """Best-effort: return string rep of simple literal defaults."""
        if isinstance(annotation_node, cst.SimpleString):
            try:
                val = ast.literal_eval(annotation_node.value)
                return str(val) if isinstance(val, str) else None
            except (ValueError, SyntaxError):
                return None
        if isinstance(annotation_node, (cst.Integer, cst.Float)):
            return annotation_node.value
        if isinstance(annotation_node, cst.Name) and annotation_node.value in (
            "True", "False", "None"
        ):
            return annotation_node.value
        return None

    def visit_AnnAssign(self, node: cst.AnnAssign) -> bool | None:
        """Collect annotated assignments inside a settings class body."""
        if not self._in_settings_class:
            return None
        if not isinstance(node.target, cst.Name):
            return None
        key = node.target.value
        # Skip private / dunder fields
        if key.startswith("_"):
            return None
        # Skip model_config (pydantic v2 SettingsConfigDict)
        if key == "model_config":
            return None
        default: str | None = None
        if node.value is not None:
            default = self._simple_default(node.value)
        pos = self.get_metadata(PositionProvider, node)
        self.found.append(
            EnvVar(
                key=key,
                default=default,
                source_file=self.source_file,
                line_number=pos.start.line,
            )
        )
        return None


def scan_file(path: Path) -> list[EnvVar]:
    """Parse one Python file and return all detected env var references."""
    try:
        source = path.read_text(encoding="utf-8")
        module = cst.parse_module(source)

        env_visitor = _EnvVarVisitor(path)
        MetadataWrapper(module).visit(env_visitor)

        settings_visitor = _PydanticSettingsVisitor(path)
        MetadataWrapper(module).visit(settings_visitor)

        return env_visitor.found + settings_visitor.found
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
