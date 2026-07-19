from datetime import datetime, timezone

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.auth.forms import LoginForm, RegisterForm
from app.extensions import db
from app.models import Setting, User
from app.services.activity_service import log_activity
from app.services.notification_service import notify

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()

        if user and user.check_password(form.password.data):
            user.last_login_at = datetime.now(timezone.utc)
            db.session.commit()
            login_user(user, remember=form.remember.data)
            log_activity(user.id, "login", "Signed in to the platform.")
            next_url = request.args.get("next")
            return redirect(next_url or url_for("dashboard.index"))

        flash("Incorrect email or password. Please try again.", "danger")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "warning")
            return render_template("auth/register.html", form=form)

        user = User(
            name=form.name.data.strip(),
            email=email,
            role=form.role.data,
            company_name=form.company_name.data.strip() or None,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()

        db.session.add(Setting(user_id=user.id))
        db.session.commit()

        notify(
            user.id, "Welcome to Yield 👋",
            "Your workspace is ready. Upload campaign data to get your first optimization.",
            "success",
        )
        log_activity(user.id, "register", "Created a new account.")

        login_user(user)
        return redirect(url_for("dashboard.index"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    log_activity(current_user.id, "logout", "Signed out of the platform.")
    logout_user()
    flash("You've been signed out.", "info")
    return redirect(url_for("auth.login"))
