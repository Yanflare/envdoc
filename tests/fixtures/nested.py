"""Fixture: env vars accessed inside a function."""

import os


def setup() -> None:
    os.getenv("REDIS_HOST", "localhost")
    os.environ.get("REDIS_PORT", "6379")
