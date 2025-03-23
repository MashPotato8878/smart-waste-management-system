from . import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    address = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False)  # New field for admin status
    reports = db.relationship('OverflowReport', backref='reporter', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Bin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='empty')  # empty, half-full, full
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    reports = db.relationship('OverflowReport', backref='bin', lazy=True)

    def update_status(self, new_status):
        self.status = new_status
        self.last_updated = datetime.utcnow()

class OverflowReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bin_id = db.Column(db.Integer, db.ForeignKey('bin.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    report_date = db.Column(db.DateTime, default=datetime.utcnow)
    photo_path = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending')  # pending, resolved
    notes = db.Column(db.Text)

class CollectionSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bin_id = db.Column(db.Integer, db.ForeignKey('bin.id'), nullable=False)
    collection_time = db.Column(db.DateTime, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def is_past_due(self):
        return datetime.utcnow() > self.collection_time

class RecyclingTip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)  # plastic, organic, electronics
    tip = db.Column(db.Text, nullable=False)
    is_do = db.Column(db.Boolean, default=True)  # True for "do", False for "don't"
    created_at = db.Column(db.DateTime, default=datetime.utcnow) 