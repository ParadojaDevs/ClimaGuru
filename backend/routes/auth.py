from flask import Blueprint, jsonify, request, make_response
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from config import Config
from models import User


auth_bp = Blueprint("auth", __name__)


def set_auth_cookies(response, access_token, refresh_token):
    """Set JWT tokens as httpOnly cookies"""
    # Access token cookie - shorter expiry for security
    response.set_cookie(
        "climaguru_access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="Lax",
        max_age=Config.JWT_ACCESS_TOKEN_EXPIRES,  # 24 hours by default
        path="/",
        domain=None  # Will be set by deployment
    )
    # Refresh token cookie - longer expiry
    response.set_cookie(
        "climaguru_refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="Lax",
        max_age=604800,  # 7 days for refresh
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

    user = User.query.filter_by(username=username).first()
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
