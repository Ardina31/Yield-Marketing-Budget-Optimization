from app.extensions import db


class Setting(db.Model):
    """Per-user preferences, kept separate from the User table by design
    (User = identity, Setting = preferences) so the identity table stays lean."""

    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    currency = db.Column(db.String(3), nullable=False, default="USD")
    timezone = db.Column(db.String(60), nullable=False, default="UTC")
    email_notifications = db.Column(db.Boolean, nullable=False, default=True)
    default_optimization_goal = db.Column(db.String(30), nullable=False, default="max_roi")

    def __repr__(self):
        return f"<Setting user_id={self.user_id}>"
