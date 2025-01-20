from flask import Flask
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:P%40ssw0rd@localhost:5432/jalin_attendance'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    from .routes import user_bp
    app.register_blueprint(user_bp, url_prefix='/users')

    with app.app_context():
        db.create_all()

    return app
