# StadiumOps — Events Ticketing & Operations

A modular Flask web application for browsing events, booking seats, and managing sales.

## Quick start

```bash
# 1. Clone the repo and create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
python run.py
```

Visit **http://127.0.0.1:5000**

## Default credentials

| Role     | Email                    | Password     |
|----------|--------------------------|--------------|
| Admin    | admin@stadiumops.com     | Admin1234!   |

> ⚠️ Change the admin password before deploying anywhere public.

## MFA setup (admin)

1. Log in as admin
2. Click **"Enable MFA"** on the dashboard
3. Scan the QR code with Google Authenticator or Authy
4. Enter the 6-digit code to confirm

Once enabled, every admin login will require a TOTP code.

## Project structure

```
stadiumops/
├── app/
│   ├── __init__.py          # App factory
│   ├── config.py            # Config profiles
│   ├── models.py            # SQLAlchemy models
│   ├── forms.py             # WTForms definitions
│   ├── blueprints/
│   │   ├── auth/            # Login, register, MFA verify
│   │   ├── tickets/         # Event browsing, seat booking
│   │   └── admin/           # Admin dashboard, sales, MFA setup
│   ├── templates/           # Jinja2 HTML templates
│   └── static/css/          # Custom stylesheet
├── tests/
│   └── test_app.py          # Pytest test suite
├── .github/workflows/ci.yml # GitHub Actions pipeline
├── requirements.txt
└── run.py                   # Development entry point
```

## Running tests

```bash
pytest tests/ -v
```

## CI/CD

Every push to `main` triggers the GitHub Actions pipeline which:
1. Installs dependencies
2. Lints with `flake8`
3. Runs the full `pytest` suite
