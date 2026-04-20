"""
Automated tests for StadiumOps — used by the CI/CD pipeline.

Run locally with:
    pytest tests/ -v
"""

import pytest
from app import create_app, db
from app.models import User, Event, Seat, Booking
from werkzeug.security import generate_password_hash


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def app():
    """Create a test application instance with an in-memory database."""
    application = create_app("testing")
    with application.app_context():
        db.create_all()
        _seed_test_data()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Return a test client for the app."""
    return app.test_client()


def _seed_test_data():
    """Insert minimal test fixtures into the in-memory database."""
    # Admin user (MFA not yet enabled so login goes straight through)
    admin = User(
        username="testadmin",
        email="admin@test.com",
        password_hash=generate_password_hash("Admin1234!"),
        is_admin=True,
        mfa_enabled=False,
    )
    # Regular customer
    customer = User(
        username="customer",
        email="customer@test.com",
        password_hash=generate_password_hash("Customer1!"),
        is_admin=False,
    )
    db.session.add_all([admin, customer])

    event = Event(
        name="Test Event",
        description="A test event",
        venue="Test Arena",
        date="2025-12-01",
    )
    db.session.add(event)
    db.session.flush()

    seat = Seat(event_id=event.id, row="A", number=1, price=10.00)
    db.session.add(seat)
    db.session.commit()


# ── Helper: log in via the test client ──────────────────────────────────────

def login(client, email, password):
    """Submit the login form and return the response."""
    return client.post(
        "/auth/login",
        data={"email": email, "password": password, "csrf_token": ""},
        follow_redirects=True,
    )


# ── Tests: public routes ─────────────────────────────────────────────────────

class TestPublicRoutes:
    """Tests that unauthenticated visitors can access public pages."""

    def test_index_loads(self, client):
        """Home page should return 200 and show event names."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"Test Event" in response.data

    def test_event_detail_loads(self, client):
        """Event detail page should show the seat grid."""
        response = client.get("/event/1")
        assert response.status_code == 200
        assert b"Row A" in response.data

    def test_login_page_loads(self, client):
        """Login page should render without errors."""
        response = client.get("/auth/login")
        assert response.status_code == 200
        assert b"Log in" in response.data

    def test_register_page_loads(self, client):
        """Registration page should render without errors."""
        response = client.get("/auth/register")
        assert response.status_code == 200


# ── Tests: authentication ────────────────────────────────────────────────────

class TestAuthentication:
    """Tests for login, logout, and registration flows."""

    def test_valid_customer_login(self, client):
        """A valid customer should be redirected to the home page after login."""
        response = login(client, "customer@test.com", "Customer1!")
        assert response.status_code == 200
        assert b"Welcome back" in response.data

    def test_invalid_password(self, client):
        """Wrong password should show an error and not log the user in."""
        response = login(client, "customer@test.com", "wrongpassword")
        assert b"Invalid email or password" in response.data

    def test_my_tickets_requires_login(self, client):
        """Unauthenticated access to /my-tickets should redirect to login."""
        response = client.get("/my-tickets", follow_redirects=True)
        assert b"Log in" in response.data

    def test_logout(self, client):
        """Logged-in user should be able to log out successfully."""
        login(client, "customer@test.com", "Customer1!")
        response = client.get("/auth/logout", follow_redirects=True)
        assert b"logged out" in response.data


# ── Tests: admin access control ──────────────────────────────────────────────

class TestAdminAccessControl:
    """Tests that admin routes are protected from non-admin users."""

    def test_admin_dashboard_requires_login(self, client):
        """Unauthenticated request to /admin/ should be denied."""
        response = client.get("/admin/", follow_redirects=True)
        # Should redirect to login, not show the dashboard
        assert b"Log in" in response.data or response.status_code == 403

    def test_customer_cannot_access_admin(self, client):
        """A logged-in customer should receive a 403 on admin routes."""
        login(client, "customer@test.com", "Customer1!")
        response = client.get("/admin/")
        assert response.status_code == 403

    def test_admin_can_access_dashboard(self, client):
        """A logged-in admin (no MFA) should see the dashboard."""
        login(client, "admin@test.com", "Admin1234!")
        response = client.get("/admin/", follow_redirects=True)
        assert response.status_code == 200
        assert b"Dashboard" in response.data


# ── Tests: booking flow ──────────────────────────────────────────────────────

class TestBookingFlow:
    """Tests for the seat booking process."""

    def test_booking_requires_login(self, client):
        """Attempting to book without being logged in should redirect to login."""
        response = client.post("/book/1", follow_redirects=True)
        assert b"Log in" in response.data

    def test_customer_can_book_seat(self, client):
        """A logged-in customer should be able to book an available seat."""
        login(client, "customer@test.com", "Customer1!")
        response = client.post("/book/1", follow_redirects=True)
        assert response.status_code == 200
        assert b"Booking confirmed" in response.data

    def test_cannot_double_book(self, client):
        """Booking the same seat twice should show a warning."""
        login(client, "customer@test.com", "Customer1!")
        client.post("/book/1", follow_redirects=True)          # first booking
        response = client.post("/book/1", follow_redirects=True)  # second attempt
        assert b"already been booked" in response.data
