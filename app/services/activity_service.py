from flask import request

from app.extensions import db
from app.models import ActivityLog


def log_activity(user_id: int, action: str, description: str) -> ActivityLog:
    entry = ActivityLog(
        user_id=user_id,
        action=action,
        description=description,
        ip_address=request.remote_addr if request else None,
    )
    db.session.add(entry)
    db.session.commit()
    return entry


def get_recent(user_id: int, limit: int = 20):
    return (
        ActivityLog.query.filter_by(user_id=user_id)
        .order_by(ActivityLog.created_at.desc())
        .limit(limit)
        .all()
    )
