# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-06-12
### Added
- Detect `python-dotenv` usage (`load_dotenv`, `dotenv_values`) and surface
  referenced `.env` file paths in generated output (closes #2)
- Handles positional path, `dotenv_path=` keyword argument, bare calls, and
  aliased imports (`from dotenv import load_dotenv as ld`)
- Handles namespace import style (`import dotenv; dotenv.load_dotenv(...)`)
- 11 new tests in `tests/test_dotenv.py`; total 50 tests, 91% coverage

## [0.2.0] - 2026-06-11

### Added
- Detect environment variables declared as annotated fields on Pydantic
  `BaseSettings` subclasses (`pydantic-settings` v2 and `pydantic` v1 compat)
- Handles aliased imports (`from pydantic_settings import BaseSettings as BS`)
- Skips private fields (`_name`) and `model_config` (pydantic v2 config dict)
- 11 new tests for BaseSettings detection; coverage 91%

## [0.1.0] - 2026-06-08

### Added
- `envdoc scan <path>` command — scans a Python codebase for env var usage
- libcst-based visitor detects `os.getenv()`, `os.environ[]`, and `os.environ.get()` patterns
- Captures key name, default value, source file, and line number for each detected variable
- `.gitignore` respect — skips files and directories matched by the nearest `.gitignore`
- `--format dotenv` output (default) — generates a documented `.env.example` with source comments
- `--format markdown` output — generates a Markdown config-reference table
- `--output <file>` flag — writes output to a file instead of stdout
- `--check` mode — exits non-zero when `.env.example` is missing or stale; CI-ready
- 27-test suite covering scanner patterns, output formats, and check mode (92% coverage)

### Infrastructure
- Hatchling build backend with `pyproject.toml`
- CI matrix (Python 3.10 / 3.11 / 3.12) via GitHub Actions
- PyPI publish workflow via OIDC trusted publisher (`release.yml`)
- ruff lint + format, mypy --strict, pytest + coverage enforcement

[Unreleased]: https://github.com/Yanflare/envdoc/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/Yanflare/envdoc/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/Yanflare/envdoc/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Yanflare/envdoc/releases/tag/v0.1.0
