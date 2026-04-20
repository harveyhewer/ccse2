from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_name="default"):
    app = Flask(__name__)

    from app.config import config_map
    app.config.from_object(config_map[config_name])

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"

    from app.blueprints.tickets import tickets_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.auth import auth_bp

    app.register_blueprint(tickets_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(auth_bp, url_prefix="/auth")

    with app.app_context():
        db.create_all()
        _seed_data()

    return app


def _seed_data():
    # only runs if db is empty, stops it adding duplicate data every restart
    from app.models import User, Event, Seat
    from werkzeug.security import generate_password_hash

    if User.query.first():
        return

    admin = User(
        username="admin",
        email="admin@stadiumops.com",
        password_hash=generate_password_hash("Admin1234!"),
        is_admin=True,
    )
    db.session.add(admin)

    event = Event(
        name="Championship Final 2025",
        description="The biggest match of the season.",
        venue="StadiumOps Arena",
        date="2025-09-20",
    )
    db.session.add(event)
    db.session.flush()

    # 4 rows, 10 seats each = 40 seats total
    # rows A+B are more expensive (closer to the front I guess)
    rows = ["A", "B", "C", "D"]
    for row in rows:
        for number in range(1, 11):
            seat = Seat(
                event_id=event.id,
                row=row,
                number=number,
                price=25.00 if row in ("A", "B") else 15.00,
            )
            db.session.add(seat)

    db.session.commit()
