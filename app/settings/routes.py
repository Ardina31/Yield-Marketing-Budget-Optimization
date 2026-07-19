from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Setting
from app.services.activity_service import get_recent, log_activity
from app.settings.forms import PasswordChangeForm, PreferencesForm, ProfileForm

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.route("/", methods=["GET"])
@login_required
def index():
    if not current_user.settings:
        db.session.add(Setting(user_id=current_user.id))
        db.session.commit()

    profile_form = ProfileForm(obj=current_user)
    preferences_form = PreferencesForm(obj=current_user.settings)
    password_form = PasswordChangeForm()
    activity = get_recent(current_user.id, limit=15)

    return render_template(
        "settings/index.html",
        profile_form=profile_form,
        preferences_form=preferences_form,
        password_form=password_form,
        activity=activity,
    )


@settings_bp.route("/profile", methods=["POST"])
@login_required
def update_profile():
    form = ProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data.strip()
        current_user.email = form.email.data.lower().strip()
        current_user.company_name = form.company_name.data.strip() or None
        db.session.commit()
        log_activity(current_user.id, "profile_update", "Updated profile information.")
        flash("Profile updated.", "success")
    else:
        flash("Please correct the errors in your profile.", "danger")
    return redirect(url_for("settings.index"))


@settings_bp.route("/preferences", methods=["POST"])
@login_required
def update_preferences():
    form = PreferencesForm()
    if form.validate_on_submit():
        setting = current_user.settings or Setting(user_id=current_user.id)
        setting.currency = form.currency.data
        setting.timezone = form.timezone.data.strip() or "UTC"
        setting.email_notifications = form.email_notifications.data
        setting.default_optimization_goal = form.default_optimization_goal.data
        db.session.add(setting)
        db.session.commit()
        flash("Preferences saved.", "success")
    else:
        flash("Please correct the errors in your preferences.", "danger")
    return redirect(url_for("settings.index"))


@settings_bp.route("/password", methods=["POST"])
@login_required
def update_password():
    form = PasswordChangeForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Your current password is incorrect.", "danger")
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            log_activity(current_user.id, "password_change", "Changed account password.")
            flash("Password updated.", "success")
    else:
        flash("Please correct the errors in the password form.", "danger")
    return redirect(url_for("settings.index"))


@settings_bp.route("/theme/<mode>", methods=["POST"])
@login_required
def set_theme(mode):
    if mode in ("light", "dark"):
        current_user.theme_preference = mode
        db.session.commit()
    return ("", 204)
