import os
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, send_file
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

from models import db, User, Resume, Analysis, Progress
from utils.pdf_parser import extract_text_from_pdf
from utils.analyzer import analyze_resume

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-for-auth-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16 MB max

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)

with app.app_context():
    db.create_all()

# --- Auth Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Dummy Data Helpers ---
class DummyAnalysis:
    score = 72
    skills = json.dumps(["Python", "SQL", "FastAPI", "React"])
    missing_skills = json.dumps(["Machine Learning", "APIs", "System Design"])
    role = "Software Engineer"
    is_dummy = True

def get_latest_analysis_or_dummy(user_id):
    analysis = Analysis.query.filter_by(user_id=user_id).order_by(Analysis.id.desc()).first()
    if analysis:
        analysis.is_dummy = False
        return analysis
    return DummyAnalysis()

# --- Routes ---
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists')
            return redirect(url_for('signup'))
            
        new_user = User(
            name=name,
            email=email,
            password=generate_password_hash(password, method='pbkdf2:sha256')
        )
        db.session.add(new_user)
        db.session.commit()
        
        session['user_id'] = new_user.id
        return redirect(url_for('dashboard'))
        
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password, password):
            flash('Please check your login details and try again.')
            return redirect(url_for('login'))
            
        session['user_id'] = user.id
        return redirect(url_for('dashboard'))
        
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    analysis = get_latest_analysis_or_dummy(user.id)
    
    skills_count = len(json.loads(analysis.skills))
    missing_count = len(json.loads(analysis.missing_skills))
        
    progress = Progress.query.filter_by(user_id=user.id).first()
    completed_len = len(json.loads(progress.completed_tasks)) if progress else 3

    # Derive breakdown dynamically so we don't need a DB migration
    breakdown = {
        'skills_match': analysis.score,
        'keywords': min(analysis.score + 10, 100),
        'formatting': 85,
        'experience': min(analysis.score + 15, 100)
    }
    
    return render_template('dashboard.html', user=user, analysis=analysis, 
                           skills_count=skills_count, missing_count=missing_count,
                           completed_len=completed_len, breakdown=breakdown,
                           active_page='dashboard')

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        if 'resume' not in request.files:
            return jsonify({'error': 'No file uploaded'})
        
        file = request.files['resume']
        if file.filename == '':
            return jsonify({'error': 'No file selected'})
            
        if file and file.filename.endswith('.pdf'):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            text = extract_text_from_pdf(filepath)
            
            new_resume = Resume(user_id=user.id, file_name=filename, extracted_text=text)
            db.session.add(new_resume)
            db.session.commit()
            
            role = request.form.get('role', 'Software Engineer')
            result = analyze_resume(text, role)
            
            new_analysis = Analysis(
                user_id=user.id,
                score=result['score'],
                skills=json.dumps(result['found_skills']),
                missing_skills=json.dumps(result['missing_skills']),
                role=role
            )
            db.session.add(new_analysis)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Resume processed successfully'
            })
        else:
            return jsonify({'error': 'Only PDF files are allowed'})
            
    return render_template('upload.html', user=user, active_page='upload')

@app.route('/skill-gap')
@login_required
def skill_gap():
    user = User.query.get(session['user_id'])
    analysis = get_latest_analysis_or_dummy(user.id)
    matched = json.loads(analysis.skills)
    missing = json.loads(analysis.missing_skills)
    return render_template('skill_gap.html', user=user, analysis=analysis, matched=matched, missing=missing, active_page='skill-gap')

@app.route('/roadmap')
@login_required
def roadmap():
    user = User.query.get(session['user_id'])
    analysis = get_latest_analysis_or_dummy(user.id)
    
    progress = Progress.query.filter_by(user_id=user.id).first()
    completed = []
    
    if hasattr(analysis, 'is_dummy') and analysis.is_dummy:
        completed = ["Learn Machine Learning"]
        roadmap_data = [{
            'week': 'Week 1-2',
            'title': 'Core missing skills',
            'tasks': ["Learn Machine Learning", "Learn APIs", "Learn System Design"]
        }]
    else:
        if not progress:
            progress = Progress(user_id=user.id, completed_tasks='[]')
            db.session.add(progress)
            db.session.commit()
        completed = json.loads(progress.completed_tasks) if progress.completed_tasks else []
        
        roadmap_data = []
        latest_resume = Resume.query.filter_by(user_id=user.id).order_by(Resume.id.desc()).first()
        if latest_resume:
            result = analyze_resume(latest_resume.extracted_text, analysis.role)
            roadmap_data = result['roadmap']
            
    return render_template('roadmap.html', user=user, analysis=analysis, roadmap_data=roadmap_data, completed=completed, active_page='roadmap')

@app.route('/api/update_progress', methods=['POST'])
@login_required
def update_progress():
    user = User.query.get(session['user_id'])
    completed_tasks = request.json.get('completed_tasks', [])
    progress = Progress.query.filter_by(user_id=user.id).first()
    if progress:
        progress.completed_tasks = json.dumps(completed_tasks)
    else:
        progress = Progress(user_id=user.id, completed_tasks=json.dumps(completed_tasks))
        db.session.add(progress)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/suggestions')
@login_required
def suggestions():
    user = User.query.get(session['user_id'])
    analysis = get_latest_analysis_or_dummy(user.id)
    
    suggestions_data = []
    if hasattr(analysis, 'is_dummy') and analysis.is_dummy:
        suggestions_data = [
            "Add a clear Education section with your degree and university.",
            "Consider learning core Software Engineer skills like Machine Learning, APIs.",
            "Use strong action verbs such as 'Developed', 'Engineered', and 'Architected'."
        ]
    else:
        latest_resume = Resume.query.filter_by(user_id=user.id).order_by(Resume.id.desc()).first()
        if latest_resume:
            result = analyze_resume(latest_resume.extracted_text, analysis.role)
            suggestions_data = result['suggestions']
            
    return render_template('suggestions.html', user=user, analysis=analysis, suggestions=suggestions_data, active_page='suggestions')

@app.route('/api/download_report', methods=['GET'])
@login_required
def download_report():
    user = User.query.get(session['user_id'])
    analysis = get_latest_analysis_or_dummy(user.id)
    
    from utils.report_generator import generate_pdf_report
    filepath = generate_pdf_report(analysis.score, analysis.role)
    if filepath and os.path.exists(filepath):
        return send_file(
            filepath,
            as_attachment=True,
            download_name="Skillora_Career_Report.pdf"
        )
    return jsonify({'error': 'Error generating report'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
