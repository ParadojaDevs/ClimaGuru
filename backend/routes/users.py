from functools import wraps

from flask import Blueprint, jsonify, request

from database import db
from models import User
from routes.auth import verify_auth_token


users_bp = Blueprint("users", __name__)


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "token requerido"}), 401

        token = auth_header.split(" ", 1)[1].strip()
        user_id = verify_auth_token(token)
        if not user_id:
            return jsonify({"error": "token invalido o expirado"}), 401

        return fn(*args, **kwargs)

    return wrapper


@users_bp.get("/users")
@require_auth
def list_users():
    users = User.query.order_by(User.id.asc()).all()
    return jsonify([user.to_dict() for user in users]), 200


@users_bp.post("/users")
@require_auth
def create_user():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "username y password son obligatorios"}), 400

    existing = User.query.filter_by(username=username).first()
    if existing:
        return jsonify({"error": "el usuario ya existe"}), 409

    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201


@users_bp.put("/users/<int:user_id>")
@require_auth
def update_user(user_id: int):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "usuario no encontrado"}), 404

    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")

    if username is not None:
        username = username.strip()
        if not username:
            return jsonify({"error": "username no puede ser vacio"}), 400

        existing = User.query.filter(User.username == username, User.id != user.id).first()
        if existing:
            return jsonify({"error": "username en uso"}), 409
        user.username = username

    if password is not None:
        if not password:
            return jsonify({"error": "password no puede ser vacio"}), 400
        user.set_password(password)

    db.session.commit()
    return jsonify(user.to_dict()), 200


@users_bp.delete("/users/<int:user_id>")
@require_auth
def delete_user(user_id: int):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "usuario no encontrado"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "usuario eliminado"}), 200
