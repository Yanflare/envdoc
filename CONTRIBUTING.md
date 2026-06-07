# Contributing to envdoc

Thanks for your interest. This is a focused tool — contributions that keep it sharp are welcome.

## Getting started

```bash
git clone https://github.com/Yanflare/envdoc
cd envdoc
pip install -e ".[dev]"
pytest
```

## Workflow

1. Open or comment on an issue before starting significant work
2. Branch from `main`: `feat/your-feature` or `fix/your-fix`
3. Follow [Conventional Commits](https://www.conventionalcommits.org/)
4. Open a PR against `main` — CI must be green

## Code standards

- `ruff check src/ tests/` — must be clean
- `mypy src/` — must pass
- `pytest` — must pass with no regressions
- Update `CHANGELOG.md` under `[Unreleased]`
