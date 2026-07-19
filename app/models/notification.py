from datetime import datetime, timezone

from app.extensions import db


class NotificationType:
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    DANGER = "danger"


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    title = db.Column(db.String(160), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    type = db.Column(db.String(20), nullable=False, default=NotificationType.INFO)
    is_read = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Notification {self.title!r} read={self.is_read}>"
