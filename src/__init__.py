from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})
    
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:P%40ssw0rd@localhost:5432/jalin_attendance'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 

    db.init_app(app)
    migrate.init_app(app, db)

    from .routes import user_bp
    app.register_blueprint(user_bp, url_prefix='/users')
    
    # kenapa ini hilang?
    with app.app_context():
        db.create_all()

    return app