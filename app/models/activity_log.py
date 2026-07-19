from datetime import datetime, timezone

from app.extensions import db


class ActivityLog(db.Model):
    """Audit trail of meaningful user actions (login, upload, optimize, export...)."""

    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    action = db.Column(db.String(60), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<ActivityLog {self.action!r} user={self.user_id}>"
