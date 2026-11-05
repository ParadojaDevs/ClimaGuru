import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-do-not-use-in-production")

    MYSQL_HOST = os.getenv("MYSQL_HOST", "100.78.215.44")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER = os.getenv("MYSQL_USER", "climaguru_app")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "dev-password-do-not-use-in-production")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "climaguru")
    MYSQL_SSL_DISABLED = os.getenv("MYSQL_SSL_DISABLED", "true").lower() == "true"

    _DEFAULT_MYSQL_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
        + ("?ssl_disabled=true" if MYSQL_SSL_DISABLED else "")
    )
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", _DEFAULT_MYSQL_URI)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173")
