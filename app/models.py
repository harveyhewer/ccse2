from datetime import datetime
from flask_login import UserMixin
from app import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    """
    Stores both admin and customer accounts.
    is_admin flag controls what they can access.
    MFA stuff (totp_secret, mfa_enabled) only really matters for admins.
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    totp_secret = db.Column(db.String(32), nullable=True)
    mfa_enabled = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    bookings = db.relationship("Booking", backref="user", lazy=True)

    def __repr__(self):
        return f"<User {self.username}>"


class Event(db.Model):
    """Represents a single event (match, concert etc.)"""

    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    venue = db.Column(db.String(128), nullable=False)
    date = db.Column(db.String(20), nullable=False)

    seats = db.relationship("Seat", backref="event", lazy=True)

    def __repr__(self):
        return f"<Event {self.name}>"


class Seat(db.Model):
    __tablename__ = "seats"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    row = db.Column(db.String(4), nullable=False)
    number = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False, default=0.0)
    is_booked = db.Column(db.Boolean, default=False, nullable=False)

    # uselist=False because a seat can only have one booking
    booking = db.relationship("Booking", backref="seat", uselist=False)

    def __repr__(self):
        return f"<Seat {self.row}{self.number} event={self.event_id}>"


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    seat_id = db.Column(db.Integer, db.ForeignKey("seats.id"), nullable=False)
    booked_at = db.Column(db.DateTime, default=datetime.utcnow)
    reference = db.Column(db.String(12), unique=True, nullable=False)

    def __repr__(self):
        return f"<Booking {self.reference}>"
