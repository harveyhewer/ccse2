"""
Tickets blueprint — customer-facing module.

Routes:
    /           - List all upcoming events.
    /event/<id> - View seats for a specific event.
    /book/<id>  - Confirm a seat booking.
    /my-tickets - View the logged-in user's bookings.
"""

import random
import string

from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app import db
from app.models import Event, Seat, Booking

tickets_bp = Blueprint(
    "tickets", __name__, template_folder="../../templates/tickets"
)


def _generate_reference(length=8):
    """
    Generate a short unique booking reference code.

    Args:
        length (int): Number of characters in the reference.

    Returns:
        str: Uppercase alphanumeric reference (e.g. 'A3FX92KL').
    """
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=length))


@tickets_bp.route("/")
def index():
    """Landing page — show all available events."""
    events = Event.query.all()
    return render_template("index.html", events=events)


@tickets_bp.route("/event/<int:event_id>")
def event_detail(event_id):
    """
    Show the seat map for a given event.
    Seats are grouped by row for the grid display.

    Args:
        event_id (int): Primary key of the event.
    """
    event = Event.query.get_or_404(event_id)

    # Group seats by row letter for template rendering
    seats_by_row = {}
    for seat in sorted(event.seats, key=lambda s: (s.row, s.number)):
        seats_by_row.setdefault(seat.row, []).append(seat)

    return render_template("event_detail.html", event=event, seats_by_row=seats_by_row)


@tickets_bp.route("/book/<int:seat_id>", methods=["POST"])
@login_required
def book_seat(seat_id):
    """
    Confirm booking for a single seat.
    Only logged-in customers can book; seat must still be available.

    Args:
        seat_id (int): Primary key of the seat to reserve.
    """
    seat = Seat.query.get_or_404(seat_id)

    # Prevent double-booking
    if seat.is_booked:
        flash("Sorry, that seat has already been booked.", "warning")
        return redirect(url_for("tickets.event_detail", event_id=seat.event_id))

    # Generate a unique reference, retrying on collision (extremely unlikely)
    reference = _generate_reference()
    while Booking.query.filter_by(reference=reference).first():
        reference = _generate_reference()

    booking = Booking(
        user_id=current_user.id,
        seat_id=seat.id,
        reference=reference,
    )
    seat.is_booked = True

    db.session.add(booking)
    db.session.commit()

    flash(f"Booking confirmed! Your reference is {reference}.", "success")
    return redirect(url_for("tickets.my_tickets"))


@tickets_bp.route("/my-tickets")
@login_required
def my_tickets():
    """Show all bookings belonging to the currently logged-in user."""
    bookings = (
        Booking.query
        .filter_by(user_id=current_user.id)
        .order_by(Booking.booked_at.desc())
        .all()
    )
    return render_template("my_tickets.html", bookings=bookings)
