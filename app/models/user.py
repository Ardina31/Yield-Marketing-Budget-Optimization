from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


class Role:
    ADMIN = "admin"
    AGENT = "agent"
    VIEWER = "viewer"

    ALL = (ADMIN, AGENT, VIEWER)
    CAN_MANAGE = (ADMIN, AGENT)  # can upload data / run optimizations


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=Role.VIEWER)
    company_name = db.Column(db.String(120), nullable=True)
    theme_preference = db.Column(db.String(10), nullable=False, default="light")
    avatar_color = db.Column(db.String(7), nullable=False, default="#0F766E")

    is_active_account = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login_at = db.Column(db.DateTime, nullable=True)

    campaigns = db.relationship(
        "Campaign", backref="owner", lazy="dynamic", cascade="all, delete-orphan"
    )
    optimization_runs = db.relationship(
        "OptimizationRun", backref="owner", lazy="dynamic", cascade="all, delete-orphan"
    )
    reports = db.relationship(
        "Report", backref="owner", lazy="dynamic", cascade="all, delete-orphan"
    )
    notifications = db.relationship(
        "Notification", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    activity_logs = db.relationship(
        "ActivityLog", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    settings = db.relationship(
        "Setting", backref="user", uselist=False, cascade="all, delete-orphan"
    )

    # Flask-Login uses .get_id() -> str(self.id) automatically via UserMixin

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password, method="pbkdf2:sha256")

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    @property
    def initials(self) -> str:
        parts = self.name.strip().split()
        if not parts:
            return "?"
        if len(parts) == 1:
            return parts[0][0].upper()
        return (parts[0][0] + parts[-1][0]).upper()

    @property
    def can_manage_data(self) -> bool:
        return self.role in Role.CAN_MANAGE

    @property
    def is_admin(self) -> bool:
        return self.role == Role.ADMIN

    def __repr__(self):
        return f"<User {self.email!r} role={self.role!r}>"
