from functools import wraps

from flask import abort, flash, redirect, url_for
from flask_login import current_user


def roles_required(*roles):
    """Restrict a view to users whose role is in `roles`.

    Usage:
        @roles_required(Role.ADMIN, Role.AGENT)
        def upload():
            ...
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))
            if current_user.role not in roles:
                flash("You do not have permission to perform this action.", "warning")
                return redirect(url_for("dashboard.index"))
            return view_func(*args, **kwargs)

        return wrapped

    return decorator


def admin_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return view_func(*args, **kwargs)

    return wrapped
