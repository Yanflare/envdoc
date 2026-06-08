"""Fixture: basic env var patterns for scanner tests."""

import os

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
SECRET_KEY = os.environ["SECRET_KEY"]
API_KEY = os.environ.get("API_KEY")
TIMEOUT = os.environ.get("TIMEOUT", "30")
