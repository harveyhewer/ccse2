"""
Entry point for running StadiumOps locally.

Usage:
    python run.py

The app will be available at http://127.0.0.1:5000
Default admin credentials: admin@stadiumops.com / Admin1234!
"""

from app import create_app

app = create_app("default")

if __name__ == "__main__":
    # debug=True enables auto-reload and detailed error pages.
    # Never run with debug=True in production.
    app.run(debug=True)
