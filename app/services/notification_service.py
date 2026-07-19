from app.extensions import db
from app.models import Notification


def notify(user_id: int, title: str, message: str, type: str = "info") -> Notification:
    note = Notification(user_id=user_id, title=title, message=message, type=type)
    db.session.add(note)
    db.session.commit()
    return note


def get_recent(user_id: int, limit: int = 8):
    return (
        Notification.query.filter_by(user_id=user_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .all()
    )


def unread_count(user_id: int) -> int:
    return Notification.query.filter_by(user_id=user_id, is_read=False).count()


def mark_all_read(user_id: int) -> None:
    Notification.query.filter_by(user_id=user_id, is_read=False).update({"is_read": True})
    db.session.commit()


def mark_read(notification_id: int, user_id: int) -> None:
    note = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
    if note:
        note.is_read = True
        db.session.commit()
