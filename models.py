from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    resumes = db.relationship('Resume', backref='user', lazy=True)
    analyses = db.relationship('Analysis', backref='user', lazy=True)
    progress = db.relationship('Progress', backref='user', lazy=True)
    applications = db.relationship('JobApplication', backref='user', lazy=True)
    saved_jobs = db.relationship('SavedJob', backref='user', lazy=True)

class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    file_name = db.Column(db.String(300), nullable=False)
    extracted_text = db.Column(db.Text, nullable=False)

class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    skills = db.Column(db.Text) # JSON string
    missing_skills = db.Column(db.Text) # JSON string
    role = db.Column(db.String(100))

class Progress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    completed_tasks = db.Column(db.Text, default="[]") # JSON string

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    company = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    salary = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=False)
    required_skills = db.Column(db.Text, nullable=False) # JSON string
    apply_link = db.Column(db.String(500), nullable=True)
    matches = db.relationship('JobApplication', backref='job', lazy=True)

class JobApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    status = db.Column(db.String(50), default="Applied") # Applied, Interview, Rejected
    match_score = db.Column(db.Integer, nullable=True)
    applied_at = db.Column(db.DateTime, server_default=db.func.now())

class SavedJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    saved_at = db.Column(db.DateTime, server_default=db.func.now())
