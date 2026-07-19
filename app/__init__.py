import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template, request
from flask_login import current_user

from config import config_by_name
from app.extensions import db, login_manager, csrf
from app.utils.formatters import register_template_filters


def create_app(config_name: str | None = None) -> Flask:
    config_name = config_name or os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))
    if hasattr(app.config, "get") and config_name == "production":
        config_by_name["production"].init_app(app)

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["REPORTS_DIR"], exist_ok=True)

    _init_extensions(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _register_context_processors(app)
    _register_logging(app)
    register_template_filters(app)

    from app import models  # noqa: F401  (ensures models are registered with SQLAlchemy)

    @app.cli.command("init-db")
    def init_db():
        """Create all database tables."""
        with app.app_context():
            db.create_all()
        print("Database tables created.")

    return app


def _init_extensions(app: Flask) -> None:
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return db.session.get(User, int(user_id))


def _register_blueprints(app: Flask) -> None:
    from app.auth.routes import auth_bp
    from app.dashboard.routes import dashboard_bp
    from app.campaigns.routes import campaigns_bp
    from app.optimization.routes import optimization_bp
    from app.reports.routes import reports_bp
    from app.settings.routes import settings_bp
    from app.api.routes import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(campaigns_bp)
    app.register_blueprint(optimization_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(api_bp)


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return render_template("errors/500.html"), 500


def _register_context_processors(app: Flask) -> None:
    @app.context_processor
    def inject_globals():
        unread = 0
        recent_notifications = []
        if current_user.is_authenticated:
            from app.services.notification_service import get_recent, unread_count
            unread = unread_count(current_user.id)
            recent_notifications = get_recent(current_user.id, limit=6)

        return {
            "app_name": app.config["APP_NAME"],
            "app_tagline": app.config["APP_TAGLINE"],
            "unread_notification_count": unread,
            "recent_notifications": recent_notifications,
            "current_path": request.path,
        }


def _register_logging(app: Flask) -> None:
    if app.debug or app.testing:
        return
    log_dir = os.path.join(app.instance_path, "logs")
    os.makedirs(log_dir, exist_ok=True)
    handler = RotatingFileHandler(os.path.join(log_dir, "app.log"), maxBytes=1_000_000, backupCount=3)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s [in %(pathname)s:%(lineno)d]"
    ))
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info("%s startup", app.config["APP_NAME"])
