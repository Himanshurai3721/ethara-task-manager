"""
wsgi.py — Gunicorn entry point for Railway deployment.

Railway runs from the repo root, so we add backend/ to sys.path
so that `from app import create_app` and `from config import ...`
resolve correctly.
"""

import sys
import os

# Make backend/ importable as the root package directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app import create_app  # noqa: E402

app = create_app()
