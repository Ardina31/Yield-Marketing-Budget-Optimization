"""
Application configuration.

All secrets and environment-specific values are read from environment
variables (see .env.example). Never hardcode credentials here.
"""
import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration shared by all environments."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'yield.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # Sessions / cookies
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_DURATION = timedelta(days=14)

    # Uploads
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB
    UPLOAD_EXTENSIONS = {".csv"}

    # Reports
    REPORTS_DIR = os.path.join(BASE_DIR, "instance", "reports")

    # Optimization defaults
    DEFAULT_TOTAL_BUDGET = 20000.0
    MIN_SPEND_FACTOR = 0.20   # a channel can shrink to 20% of its current spend
    MAX_SPEND_FACTOR = 3.00   # a channel can grow to 300% of its current spend

    # Pagination
    CAMPAIGNS_PER_PAGE = 10

    APP_NAME = "Yield"
    APP_TAGLINE = "Marketing Budget Optimization Platform"

    WTF_CSRF_TIME_LIMIT = None


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True

    @classmethod
    def init_app(cls, app):
        if app.config["SECRET_KEY"] == "dev-secret-key-change-me":
            raise RuntimeError(
                "SECRET_KEY must be set via environment variable in production."
            )


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
