from flask import Blueprint, jsonify, request, make_response, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from models import User
import logging


auth_bp = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)


def set_auth_cookies(response, access_token, refresh_token):
    """Set JWT tokens as httpOnly cookies"""
    is_secure = current_app.config.get("ENV") == "production"
    # Access token cookie - shorter expiry for security
    response.set_cookie(
        "climaguru_access_token",
        value=access_token,
        httponly=True,
        secure=is_secure,
        samesite="Lax",
        max_age=current_app.config.get("JWT_ACCESS_TOKEN_EXPIRES", 86400),
        path="/",
        domain=None
    )
    # Refresh token cookie - longer expiry
    response.set_cookie(
        "climaguru_refresh_token",
        value=refresh_token,
        httponly=True,
        secure=is_secure,
        samesite="Lax",
        max_age=604800,
        path="/",
        domain=None
    )
    return response


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "username y password son obligatorios"}), 400

    try:
        user = User.query.filter_by(username=username).first()
        logger.info(f"Login attempt for user: {username}, found: {user is not None}")
        if user:
            logger.info(f"User password_hash: {user.password_hash[:20]}...")
            logger.info(f"Check password result: {user.check_password(password)}")
        if not user or not user.check_password(password):
            return jsonify({"error": "credenciales invalidas"}), 401

        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)

        response = jsonify({
            "token": access_token,
            "refresh_token": refresh_token,
            "user": user.to_dict()
        }), 200

        return set_auth_cookies(response, access_token, refresh_token)
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        return jsonify({"error": "error interno del servidor"}), 500
