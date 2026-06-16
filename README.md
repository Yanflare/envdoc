# envdoc
> Your .env.example should write itself.

[![codecov](https://codecov.io/github/Yanflare/envdoc/graph/badge.svg)](https://codecov.io/github/Yanflare/envdoc)
[![CI](https://github.com/Yanflare/envdoc/actions/workflows/ci.yml/badge.svg)](https://github.com/Yanflare/envdoc/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/envdoc)](https://pypi.org/project/envdoc/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

I keep noticing the same pattern in Python projects, where environment variable documentation is
incomplete, outdated, or missing entirely, so I built a solution which eliminates config errors by
scanning your codebase and generating the documentation that should have been there already.

$ envdoc scan ./src
Found 7 environment variables in 12 files

ANTHROPIC_API_KEY     src/llm/client.py:14

DATABASE_URL          src/db/connection.py:8

LOG_LEVEL             src/app.py:22

PORT                  src/app.py:31

REDIS_URL             src/cache.py:11

SECRET_KEY            src/auth.py:9

SENTRY_DSN            src/monitoring.py:4

Generated: .env.example

---

## Install

```bash
pip install envdoc
```

## Features

```bash
# Scan and write .env.example
envdoc scan ./src

# Markdown config reference (for docs)
envdoc scan ./src --format markdown

# CI mode — exit 1 if .env.example is stale
envdoc scan ./src --check

# Write to a specific file
envdoc scan ./src --output docs/config.md --format markdown
```

### CI integration

```yaml
- name: Check .env.example is up to date
  run: envdoc scan ./src --check
```

Any new env var added to the codebase without updating `.env.example` fails the build.

---

## Roadmap

- [x] Core scanner: `os.getenv`, `os.environ`
- [ ] [#2](../../issues/2) Pydantic `BaseSettings` detection
- [ ] [#3](../../issues/3) `python-dotenv` `load_dotenv` key detection
- [ ] [#4](../../issues/4) pre-commit hook integration
- [ ] [#5](../../issues/5) Nested env access in f-strings
- [ ] [#6](../../issues/6) GitHub Action wrapper

---

## Contributing

Bug reports and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT — see [LICENSE](LICENSE).
