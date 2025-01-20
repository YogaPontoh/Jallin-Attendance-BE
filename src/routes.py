from flask import Blueprint, request, jsonify
from .models import User
from . import db

user_bp = Blueprint('user', __name__)

@user_bp.route('', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data.get('name') or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Name, email, and password are required."}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email already exists."}), 400

    new_user = User(name=data['name'], email=data['email'], password=data['password'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User created successfully.", "user": new_user.to_dict()}), 201

@user_bp.route('', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users]), 200

@user_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404
    return jsonify(user.to_dict()), 200

