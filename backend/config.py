"""
Configuration for Team Task Manager.

Set FLASK_ENV=production to switch to ProductionConfig.
All secrets should be provided via environment variables in production.
"""

import os
from datetime import timedelta


class Config:
    # ── security ──────────────────────────────────────────────────────────────
    SECRET_KEY     = os.environ.get("SECRET_KEY",     "change-me-in-production")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", SECRET_KEY)

    # ── database ──────────────────────────────────────────────────────────────
    # SQLite path is relative to the instance/ folder Flask creates automatically.
    SQLALCHEMY_DATABASE_URI    = os.environ.get("DATABASE_URL", "sqlite:///teamtask.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── misc ──────────────────────────────────────────────────────────────────
    JSON_SORT_KEYS = False


class DevelopmentConfig(Config):
    DEBUG            = True
    SQLALCHEMY_ECHO  = False   # set True to log all SQL


class ProductionConfig(Config):
    DEBUG           = False
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    TESTING                  = True
    SQLALCHEMY_DATABASE_URI  = "sqlite:///:memory:"
    SQLALCHEMY_ECHO          = False


_configs = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "testing":     TestingConfig,
}


def get_config():
    env = os.environ.get("FLASK_ENV", "development")
    return _configs.get(env, DevelopmentConfig)
