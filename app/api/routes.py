from flask import Blueprint, jsonify
from flask_login import current_user, login_required

from app.services.notification_service import mark_all_read, mark_read, unread_count

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/notifications/unread-count")
@login_required
def notifications_unread_count():
    return jsonify({"count": unread_count(current_user.id)})


@api_bp.route("/notifications/<int:notification_id>/read", methods=["POST"])
@login_required
def notifications_mark_read(notification_id):
    mark_read(notification_id, current_user.id)
    return jsonify({"status": "ok"})


@api_bp.route("/notifications/read-all", methods=["POST"])
@login_required
def notifications_mark_all_read():
    mark_all_read(current_user.id)
    return jsonify({"status": "ok"})
