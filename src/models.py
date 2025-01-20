from . import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(120), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "password": self.password
        }

class Attendance_history(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    check_in_time = db.Column(db.DateTime, nullable=False)
    check_out_time = db.Column(db.DateTime, nullable=False)
    check_in_asset = db.Column(db.String(120), nullable=False)
    check_out_asset = db.Column(db.String(120), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.name,
            "check_in_time": self.check_in_time,
            "check_out_time": self.check_out_time,
            "check_in_asset": self.check_in_asset,
            "check_out_asset": self.check_out_asset
        }
