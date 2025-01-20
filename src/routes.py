from flask import Blueprint, request, jsonify
from .models import User
from . import db

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

    if not data.get('name') or not data.get('password'):
        return jsonify({"error": "Username or password salah"}), 400
    
    user = User.query.filter_by(username=data.get('name')).first()

    if not user or not (user.password, data.get('password')):
        return jsonify({"error": "Invalid username or password"}), 401

    return jsonify({"message": "Login successful", "user": user.to_dict()}), 200


# Endpoint: Get list of users (Admin only)
@user_bp.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    user_list = [{"id": user.id, "username": user.username, "password": user.password} for user in users]
    return jsonify(user_list), 200

# Endpoint: Get attendance report (Admin only)
@user_bp.route('/report', methods=['GET'])
def get_report():
    # Query untuk mendapatkan laporan dengan username
    reports = (
        db.session.query(
            User.username,
            Attendance_history.date,
            Attendance_history.check_in_time,
            Attendance_history.check_out_time
        )
        .join(User, Attendance_history.user_id == User.id)
        .all()
    )

    # Membentuk respons JSON
    report_list = [
        {
            "username": report.username,
            "date": report.date.strftime('%Y-%m-%d'),
            "check_in_time": report.check_in_time.strftime('%H:%M:%S') if report.check_in_time else None,
            "check_out_time": report.check_out_time.strftime('%H:%M:%S') if report.check_out_time else None
        }
        for report in reports
    ]

    return jsonify(report_list), 200

@user_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404
    return jsonify(user.to_dict()), 200

