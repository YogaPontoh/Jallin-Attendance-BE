from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import jwt
from .models import User, Attendance_history
from . import db
from datetime import datetime, timedelta
from io import BytesIO
import os
import base64

SECRET_KEY = "your-secret-key"

user_bp = Blueprint('user', __name__)

@user_bp.route('', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data.get('username') or not data.get('password'):
        return jsonify({"error": "Username and password are required."}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "Username already exists."}), 400

    if data.get('role') != 'admin' and data.get('role') != 'user':
        return jsonify({"error": "Role yang dimasukan salah"}), 400

    new_user = User(username=data['username'], password=data['password'], role=data['role'])
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

    token = jwt.encode(
        {
            "user_id": user.id,
            "username": user.username,
            "role": user.role,
            "exp": datetime.utcnow() + timedelta(minutes=15)
        },
        SECRET_KEY,
        algorithm="HS256"
    )

    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": user.to_dict()
    }), 200

@user_bp.route('/checkin', methods=['POST'])
def checkin():
    data = request.get_json()
    user_id = data.get('user_id')
    photo_path = data.get('photo_path')

    if not user_id:
        return jsonify({"error": "User ID is required."}), 400
    
    if not photo_path:
        return jsonify({"error": "Photo path is required"})

    today = datetime.now().date()
    attendance = Attendance_history.query.filter_by(user_id=user_id, date=today).first()
    if attendance:
        return jsonify({"error": "User already checked in today."}), 400

    new_attendance = Attendance_history(
        user_id=user_id,
        date=today,
        check_in_time=datetime.now(),
        check_in_photo=photo_path
    )
    db.session.add(new_attendance)
    db.session.commit()

    return jsonify({"message": "Check-in successful."}), 200

@user_bp.route('/checkout', methods=['POST'])
def checkout():
    data = request.get_json()
    user_id = data.get('user_id')
    photo_path = data.get('photo_path')

    if not user_id:
        return jsonify({"error": "User ID is required."}), 400
    
    if not photo_path:
        return jsonify({"error": "Photo path is required"}), 400

    pending_checkin = Attendance_history.query.filter_by(user_id=user_id, check_out_time=None).first()
    if not pending_checkin:
        return jsonify({"error": "User has no pending check-in to check out from."}), 400
    
    if pending_checkin.check_out_time:
        return jsonify({"error": "User already checked out today"}), 400

    pending_checkin.check_out_time = datetime.now()
    pending_checkin.check_out_photo = photo_path
    db.session.commit()

    return jsonify({"message": "Check-out successful."}), 200

@user_bp.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    user_list = [{"id": user.id, "username": user.username, "password": user.password} for user in users]
    return jsonify(user_list), 200

@user_bp.route('/report', methods=['GET'])
def get_report():
    reports = (
        db.session.query(
            User.username,
            Attendance_history.date,
            Attendance_history.check_in_time,
            Attendance_history.check_out_time,
            Attendance_history.check_in_photo,
            Attendance_history.check_out_photo
        )
        .join(User, Attendance_history.user_id == User.id)
        .all()
    )

    report_list = [
        {
            "username": report.username,
            "date": report.date.strftime('%Y-%m-%d'),
            "check_in_time": report.check_in_time.strftime('%H:%M:%S') if report.check_in_time else None,
            "check_out_time": report.check_out_time.strftime('%H:%M:%S') if report.check_out_time else None,
            "check_in_photo": report.check_in_photo,
            "check_out_photo": report.check_out_photo
        }
        for report in reports
    ]

    return jsonify(report_list), 200

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@user_bp.route('/upload-photo', methods=['POST'])
def upload_photo():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        return jsonify({"message": "File uploaded successfully", "file_path": file_path}), 200

    return jsonify({"error": "File not allowed"}), 400

@user_bp.route('/file-to-base64', methods=['POST'])
def file_to_base64():
    data = request.get_json()
    file_path = data.get('file_path')

    if not file_path:
        return jsonify({"error": "File path is required"}), 400

    full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_path)
    if not os.path.exists(full_path):
        return jsonify({"error": f"File not found: {file_path}"}), 404

    try:
        with open(full_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

        return jsonify({
            "message": "File converted to Base64 successfully",
            "file_base64": encoded_string
        }), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
