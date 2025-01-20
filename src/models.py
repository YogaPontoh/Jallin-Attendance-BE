from . import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(120), nullable=False)

    # Relasi One-to-Many ke Attendance_history
    histories = db.relationship('Attendance_history', back_populates='user', cascade='all, delete')

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "password": self.password,
            "histories": [history.to_dict() for history in self.histories]
        }

class Attendance_history(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    check_in_time = db.Column(db.DateTime, nullable=False)
    check_out_time = db.Column(db.DateTime, nullable=True)
    check_in_photo = db.Column(db.String(255))
    check_out_photo = db.Column(db.String(255))

    # Relasi balik ke User
    user = db.relationship('User', back_populates='histories')

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "date": self.date,
            "check_in_time": self.check_in_time.isoformat() if self.check_in_time else None,
            "check_out_time": self.check_out_time.isoformat() if self.check_out_time else None,
        }