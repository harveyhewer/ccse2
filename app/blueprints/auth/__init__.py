"""
Authentication blueprint.

Handles:
    - Customer registration
    - Login (with MFA step for admin users)
    - Logout
"""

from flask import Blueprint, render_template, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import pyotp

from app import db
from app.models import User
from app.forms import LoginForm, RegisterForm, MFAVerifyForm

# Create the blueprint; URL prefix '/auth' is applied in the factory
auth_bp = Blueprint("auth", __name__, template_folder="../../templates/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    Customer registration.
    Admins are created via the seed function or directly in the DB.
    """
    if current_user.is_authenticated:
        return redirect(url_for("tickets.index"))

    form = RegisterForm()
    if form.validate_on_submit():
        # Check email is not already taken
        existing = User.query.filter_by(email=form.email.data).first()
        if existing:
            flash("An account with that email already exists.", "danger")
            return render_template("register.html", form=form)

        # Hash the password before storing
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            is_admin=False,
        )
        db.session.add(user)
        db.session.commit()
        flash("Account created — please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Login page.
    Admin users are redirected to a second MFA verification step.
    """
    if current_user.is_authenticated:
        return redirect(url_for("tickets.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        # Validate credentials
        if not user or not check_password_hash(user.password_hash, form.password.data):
            flash("Invalid email or password.", "danger")
            return render_template("login.html", form=form)

        if user.is_admin and user.mfa_enabled:
            # Store user id in session temporarily; MFA must be verified before
            # the user is fully logged in
            session["pending_user_id"] = user.id
            return redirect(url_for("auth.mfa_verify"))

        # Non-admin or admin without MFA set up yet
        login_user(user, remember=form.remember.data)
        flash(f"Welcome back, {user.username}!", "success")
        return redirect(url_for("tickets.index"))

    return render_template("login.html", form=form)


@auth_bp.route("/mfa-verify", methods=["GET", "POST"])
def mfa_verify():
    """
    MFA verification step for admin users.
    Checks the TOTP code from their authenticator app.
    """
    pending_id = session.get("pending_user_id")
    if not pending_id:
        return redirect(url_for("auth.login"))

    user = User.query.get(pending_id)
    form = MFAVerifyForm()

    if form.validate_on_submit():
        totp = pyotp.TOTP(user.totp_secret)
        if totp.verify(form.token.data):
            session.pop("pending_user_id", None)
            login_user(user)
            flash("MFA verified. Welcome, admin!", "success")
            return redirect(url_for("admin.dashboard"))
        else:
            flash("Invalid MFA code. Please try again.", "danger")

    return render_template("mfa_verify.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    """Log the current user out and redirect to the login page."""
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
