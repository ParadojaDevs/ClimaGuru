from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from database import db
from models import User


users_bp = Blueprint("users", __name__)


@users_bp.get("/users")
@jwt_required()
def list_users():
    user_id = get_jwt_identity()
    users = User.query.order_by(User.id.asc()).all()
    return jsonify([user.to_dict() for user in users]), 200


@users_bp.post("/users")
@jwt_required()
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
@jwt_required()
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
@jwt_required()
def delete_user(user_id: int):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "usuario no encontrado"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "usuario eliminado"}), 200
