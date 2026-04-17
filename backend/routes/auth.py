from flask import Blueprint, jsonify, request
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from config import Config
from models import User


auth_bp = Blueprint("auth", __name__)


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(Config.SECRET_KEY)


def create_auth_token(user_id: int) -> str:
    return _serializer().dumps({"user_id": user_id}, salt="auth")


def verify_auth_token(token: str, max_age: int = 86400) -> int | None:
    try:
        payload = _serializer().loads(token, salt="auth", max_age=max_age)
        return payload.get("user_id")
    except (BadSignature, SignatureExpired):
        return None


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

    token = create_auth_token(user.id)
    return jsonify({"token": token, "user": user.to_dict()}), 200
