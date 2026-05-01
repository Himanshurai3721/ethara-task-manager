"""
config.py — Application configuration.

Railway environment variables to set:
    SECRET_KEY      (required in production)
    JWT_SECRET_KEY  (optional, falls back to SECRET_KEY)
    DATABASE_URL    (optional, defaults to SQLite)
    FLASK_ENV       (optional, defaults to "production")
"""

import os


class Config:
    SECRET_KEY     = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or os.environ.get("SECRET_KEY", "dev-secret-change-in-production")

    # Railway injects DATABASE_URL for Postgres add-ons.
    # Falls back to SQLite stored in /tmp (ephemeral but fine for demos).
    _db_url = os.environ.get("DATABASE_URL", "")
    # Railway Postgres URLs start with postgres:// — SQLAlchemy needs postgresql://
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI    = _db_url or "sqlite:////tmp/teamtask.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JSON_SORT_KEYS = False
    DEBUG  = False
    TESTING = False


class DevelopmentConfig(Config):
    DEBUG           = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///teamtask.db")


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


_configs = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "testing":     TestingConfig,
}


def get_config():
    # Default to production so Railway works without setting FLASK_ENV
    env = os.environ.get("FLASK_ENV", "production")
    return _configs.get(env, ProductionConfig)
