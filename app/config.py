import os


class DefaultConfig:
    # TODO: make sure SECRET_KEY is set properly before deployment
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")

    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASEDIR, "..", "stadiumops.db"),
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False  # keeps getting deprecated warnings without this

    WTF_CSRF_ENABLED = True

    # stops js being able to read the session cookie
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"


class TestingConfig(DefaultConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False  # csrf makes writing tests a nightmare so turning it off here
    LOGIN_DISABLED = False


config_map = {
    "default": DefaultConfig,
    "testing": TestingConfig,
}
