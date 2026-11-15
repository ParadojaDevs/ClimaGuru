import os
from datetime import timedelta
from functools import cached_property


class Config:
    @cached_property
    def SECRET_KEY(self):
        val = os.getenv("SECRET_KEY")
        if not val:
            raise RuntimeError("SECRET_KEY must be set in environment")
        return val

    @cached_property
    def JWT_ACCESS_TOKEN_EXPIRES(self):
        val = os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "86400")
        return int(val)

    @cached_property
    def MYSQL_HOST(self):
        return os.getenv("MYSQL_HOST")

    @cached_property
    def MYSQL_PORT(self):
        return int(os.getenv("MYSQL_PORT", "3306"))

    @cached_property
    def MYSQL_USER(self):
        return os.getenv("MYSQL_USER")

    @cached_property
    def MYSQL_PASSWORD(self):
        return os.getenv("MYSQL_PASSWORD")

    @cached_property
    def MYSQL_DATABASE(self):
        return os.getenv("MYSQL_DATABASE")

    @cached_property
    def MYSQL_SSL_DISABLED(self):
        return os.getenv("MYSQL_SSL_DISABLED", "true").lower() == "true"

    @cached_property
    def SQLALCHEMY_DATABASE_URI(self):
        if not all([self.MYSQL_HOST, self.MYSQL_USER, self.MYSQL_PASSWORD, self.MYSQL_DATABASE]):
            raise RuntimeError("MySQL configuration incomplete: set MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE")

        uri = os.getenv("DATABASE_URL")
        if uri:
            return uri

        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
            + ("?ssl_disabled=true" if self.MYSQL_SSL_DISABLED else "")
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @cached_property
    def CORS_ORIGINS(self):
        return os.getenv("CORS_ORIGINS", "http://localhost:5173")