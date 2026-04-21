"""

Routes:
    /admin/             - Dashboard with booking overview.
    /admin/sales        - Full sales/booking list.
    /admin/mfa-setup    - TOTP MFA setup for the admin account.
    /admin/cancel/<id>  - Cancel a booking.
"""

import io
import base64

import pyotp
import qrcode

from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app import db
from app.models import Booking, Event, Seat
from app.forms import MFASetupForm

admin_bp = Blueprint("admin", __name__, template_folder="../../templates/admin")


def admin_required(func):
    """
    Decorator that restricts a route to admin users only.
    Returns 403 Forbidden if the current user is not an admin.
    """
    from functools import wraps

    @wraps(func)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return func(*args, **kwargs)

    return decorated


@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    """
    Admin dashboard.
    Shows summary statistics: total events, seats sold, revenue.
    """
    total_events = Event.query.count()
    total_bookings = Booking.query.count()
    total_seats = Seat.query.count()

    # Calculate total revenue from all confirmed bookings
    booked_seats = Seat.query.filter_by(is_booked=True).all()
    total_revenue = sum(s.price for s in booked_seats)

    recent_bookings = (
        Booking.query.order_by(Booking.booked_at.desc()).limit(10).all()
    )

    return render_template(
        "dashboard.html",
        total_events=total_events,
        total_bookings=total_bookings,
        total_seats=total_seats,
        total_revenue=total_revenue,
        recent_bookings=recent_bookings,
    )


@admin_bp.route("/sales")
@login_required
@admin_required
def sales():
    """Full list of all bookings with customer and seat details."""
    bookings = Booking.query.order_by(Booking.booked_at.desc()).all()
    return render_template("sales.html", bookings=bookings)


@admin_bp.route("/cancel/<int:booking_id>", methods=["POST"])
@login_required
@admin_required
def cancel_booking(booking_id):
    """
    Cancel a booking and free up the seat.

    Args:
        booking_id (int): Primary key of the booking to cancel.
    """
    booking = Booking.query.get_or_404(booking_id)
    booking.seat.is_booked = False
    db.session.delete(booking)
    db.session.commit()
    flash(f"Booking {booking.reference} has been cancelled.", "info")
    return redirect(url_for("admin.sales"))


@admin_bp.route("/mfa-setup", methods=["GET", "POST"])
@login_required
@admin_required
def mfa_setup():
    """
    TOTP MFA setup page for the admin user.
    Generates a TOTP secret, displays a QR code, and verifies a test code
    before enabling MFA on the account.
    """
    form = MFASetupForm()

    # Generate or retrieve a provisioning TOTP secret
    if not current_user.totp_secret:
        current_user.totp_secret = pyotp.random_base32()
        db.session.commit()

    totp = pyotp.TOTP(current_user.totp_secret)
    provisioning_uri = totp.provisioning_uri(
        name=current_user.email,
        issuer_name="StadiumOps",
    )

    # Generate QR code and encode as base64 for inline <img> display
    qr_img = qrcode.make(provisioning_uri)
    buffer = io.BytesIO()
    qr_img.save(buffer, format="PNG")
    qr_b64 = base64.b64encode(buffer.getvalue()).decode()

    if form.validate_on_submit():
        # Verify the code entered matches the current TOTP window
        if totp.verify(form.token.data):
            current_user.mfa_enabled = True
            db.session.commit()
            flash("MFA has been enabled on your account.", "success")
            return redirect(url_for("admin.dashboard"))
        else:
            flash("Invalid code — please try again.", "danger")

    return render_template(
        "mfa_setup.html",
        form=form,
        qr_b64=qr_b64,
        secret=current_user.totp_secret,
    )
