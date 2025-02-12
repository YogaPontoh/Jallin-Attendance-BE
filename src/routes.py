from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename
from .models import User, Attendance_history
from . import db
from datetime import datetime, timedelta
from io import BytesIO
import os
import base64
import pandas as pd
import io
import jwt
from sqlalchemy import desc

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

    if not user:
        return jsonify({"error": "Invalid username or password"}), 401
    
    if not (user.password == data.get('password')):
        return jsonify({"error": "Invalid password"}), 401

    token = jwt.encode(
        {
            "user_id": user.id,
            "username": user.username,
            "role": user.role,
            "exp": datetime.now() + timedelta(minutes=15)
        },
        SECRET_KEY,
        algorithm="HS256"
    )

    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": user.to_dict()
    }), 200

@user_bp.route('/attendance-status', methods=['GET'])
def attendace_status():
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({"error": "user_id tidak di isi"}), 400
    
    user = User.query.filter_by(id=user_id).first()
    
    if not user:
        return jsonify({"error": "user_id tidak di temukan"}), 400
    
    last_checkin = Attendance_history.query.filter(
        Attendance_history.check_out_time.is_(None) & (Attendance_history.user_id == user.id)
    ).order_by(
        desc(Attendance_history.check_in_time)
    ).first()
    
    return jsonify({
        "last_checkin": last_checkin.check_in_time if last_checkin else None,
        "last_checkout": last_checkin.check_out_time if last_checkin else None
    })

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

    return jsonify({"message": "Check-in successful.", "status": "check-in"}), 200

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
    department = request.args.get('department')
    print("Departemen yang diterima:", department)
    
    query = db.session.query(
            User.name,
            User.department,
            Attendance_history.date,
            Attendance_history.check_in_time,
            Attendance_history.check_out_time,
            Attendance_history.check_in_photo,
            Attendance_history.check_out_photo
        ).join(User, Attendance_history.user_id == User.id)
        
    if department:
            query = query.filter(User.department == department)
    
    reports = query.all()
    
    base_url = request.host_url

    report_list = [
        {
            "name": report.name,
            "department": report.department,
            "date": report.date.strftime('%Y-%m-%d'),
            "check_in_time": report.check_in_time.strftime('%H:%M:%S') if report.check_in_time else None,
            "check_out_time": report.check_out_time.strftime('%H:%M:%S') if report.check_out_time else None,
            "check_in_photo": report.check_in_photo if report.check_in_photo else None,
            "check_out_photo": report.check_out_photo if report.check_out_photo else None,
            "hours_worked": calculate_hours_worked(report.check_in_time, report.check_out_time),
            "overtime": calculate_overtime(report.check_in_time, report.check_out_time)
        }
        for report in reports
    ]

    return jsonify(report_list), 200
    
def calculate_hours_worked(check_in_time, check_out_time):
    """
    Menghitung durasi jam kerja dan mengembalikannya dalam format HH:MM.
    """
    if not check_in_time or not check_out_time:
        return "Belum Checkout"
    
    duration = check_out_time - check_in_time
    total_seconds = duration.total_seconds()
    
    hours, remainder = divmod(total_seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    return f"{int(hours):02d}:{int(minutes):02d}"


def calculate_overtime(check_in_time, check_out_time):
    """
    Menghitung jam lembur
    """
    if not check_in_time or not check_out_time:
        return "Belum Checkout"
    
    duration = check_out_time - check_in_time
    total_seconds = duration.total_seconds()
    
    hours, remainder = divmod(total_seconds-32400, 3600)
    minutes, _ = divmod(remainder, 60)
    
    if hours < 0:
        return "0"
    else:
        return f"{int(hours):02d}:{int(minutes):02d}"
    
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

    full_path = os.path.join(file_path)
    if not os.path.exists(full_path):
        return jsonify({"error": "File not found: {file_path}"}), 404

    try:
        with open(full_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

        return jsonify({
            "message": "File converted to Base64 successfully",
            "file_base64": encoded_string
        }), 200
    except Exception as e:
        return jsonify({"error": "An error occurred: {str(e)}"}), 500

@user_bp.route('/report/download', methods=['GET'])
def download_report():
    department = request.args.get('department')
    query = db.session.query(
            User.name,
            User.department,
            Attendance_history.date,
            Attendance_history.check_in_time,
            Attendance_history.check_out_time,
            Attendance_history.check_in_photo,
            Attendance_history.check_out_photo
        ).join(User, Attendance_history.user_id == User.id)
        
    if department:
        query = query.filter(User.department == department)

    reports = query.all()

    data = [
        {
            "Name": report.name,
            "Department": report.department,
            "Date": report.date.strftime('%Y-%m-%d'),
            "Check-In Time": report.check_in_time.strftime('%H:%M:%S') if report.check_in_time else None,
            "Check-Out Time": report.check_out_time.strftime('%H:%M:%S') if report.check_out_time else None,
            "Hours Worked": calculate_hours_worked(report.check_in_time, report.check_out_time),
            "Overtime": calculate_overtime(report.check_in_time, report.check_out_time)
        }
        for report in reports
    ]

    df = pd.DataFrame(data)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Report')

    output.seek(0)

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'attendance_report_{department or "all"}.xlsx'
    )