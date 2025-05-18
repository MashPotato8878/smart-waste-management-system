from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
import os
from datetime import datetime

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure the upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Configure SQLite database with a persistent file
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///waste_management.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register blueprints
    from .routes import main_bp, auth_bp, api_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    # Create database tables and initial data
    with app.app_context():
        db.create_all()
        from .models import User, Bin
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            # Add initial bins
            initial_bins = [
                Bin(
                    location='Main Street Corner',
                    latitude=3.1412,
                    longitude=101.6865,
                    status='empty',
                    last_updated=datetime.utcnow()
                ),
                Bin(
                    location='Park Avenue',
                    latitude=3.1412,
                    longitude=101.6865,
                    status='half-full',
                    last_updated=datetime.utcnow()
                ),
                Bin(
                    location='Shopping Mall Entrance',
                    latitude=3.1412,
                    longitude=101.6865,
                    status='full',
                    last_updated=datetime.utcnow()
                )
            ]
            db.session.add_all(initial_bins)
            db.session.commit()
            print('Database initialized successfully with admin user and initial bins.')
        else:
            # Ensure admin user always has is_admin=True
            admin.is_admin = True
            db.session.commit()
            print('Database already initialized with admin user. Ensured is_admin=True.')

    return app 