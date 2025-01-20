from flask import Blueprint, request, jsonify
from .models import User, Attendance_history
from . import db
from datetime import datetime

user_bp = Blueprint('user', __name__)

@user_bp.route('', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data.get('username') or not data.get('password'):
        return jsonify({"error": "Username and password are required."}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "Username already exists."}), 400

    new_user = User(username=data['username'], password=data['password'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User created successfully.", "user": new_user.to_dict()}), 201

@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data.get('username') or not data.get('password'):
        return jsonify({"error": "Username or password salah"}), 400
    
    user = User.query.filter_by(username=data.get('username')).first()

    if not user or not (user.password, data.get('password')):
        return jsonify({"error": "Invalid username or password"}), 401

    return jsonify({"message": "Login successful", "user": user.to_dict()}), 200

@user_bp.route('/checkin', methods=['POST'])
def checkin():
    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({"error": "User ID is required."}), 400

    # Check if user has already checked in today
    today = datetime.now().date()
    attendance = Attendance_history.query.filter_by(user_id=user_id, date=today).first()
    if attendance:
        return jsonify({"error": "User already checked in today."}), 400

    # Save check-in
    new_attendance = Attendance_history(user_id=user_id, date=today, check_in_time=datetime.now())
    db.session.add(new_attendance)
    db.session.commit()

    return jsonify({"message": "Check-in successful."}), 200

# Endpoint: Check-out
@user_bp.route('/checkout', methods=['POST'])
def checkout():
    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({"error": "User ID is required."}), 400

    # Cek apakah user memiliki riwayat check-in sebelumnya tanpa checkout
    pending_checkin = Attendance_history.query.filter_by(user_id=user_id, check_out_time=None).first()
    if not pending_checkin:
        return jsonify({"error": "User has no pending check-in to check out from."}), 400

    # Simpan waktu checkout untuk entri check-in yang belum selesai
    pending_checkin.check_out_time = datetime.now()
    db.session.commit()

    return jsonify({"message": "Check-out successful."}), 200

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

