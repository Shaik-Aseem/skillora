import os
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, send_file
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

from models import db, User, Resume, Analysis, Progress, Job, JobApplication, SavedJob
from utils.pdf_parser import extract_text_from_pdf
from utils.analyzer import analyze_resume
from services.job_api import fetch_real_jobs

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
    
    # Auto-seed mock jobs
    if not Job.query.first():
        dummy_jobs = [
            {"title": "Software Engineer", "company": "TechNova", "location": "Remote", "salary": "$120k", "description": "Looking for a Python/React developer.", "required_skills": '["Python", "React", "SQL"]', "apply_link": "#"},
            {"title": "Machine Learning Engineer", "company": "AI Dynamics", "location": "New York, NY", "salary": "$150k", "description": "Build predictive models.", "required_skills": '["Python", "Machine Learning", "TensorFlow", "SQL"]', "apply_link": "#"},
            {"title": "Data Analyst", "company": "FinData", "location": "Chicago, IL", "salary": "$90k", "description": "Analyze financial data trends.", "required_skills": '["SQL", "Python", "Tableau", "Excel"]', "apply_link": "#"},
            {"title": "Frontend Developer", "company": "Pixel Web", "location": "San Francisco, CA", "salary": "$110k", "description": "Create stunning user interfaces.", "required_skills": '["Javascript", "React", "CSS", "HTML5"]', "apply_link": "#"},
            {"title": "Backend Systems Architect", "company": "CloudScale", "location": "Austin, TX", "salary": "$140k", "description": "Design scalable infrastructure.", "required_skills": '["Python", "FastAPI", "Docker", "System Design", "AWS"]', "apply_link": "#"},
        ]
        for j in dummy_jobs:
            db.session.add(Job(**j))
        db.session.commit()

# --- Auth Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Global Data Bounds ---
def get_user_analysis(user_id):
    return Analysis.query.filter_by(user_id=user_id).order_by(Analysis.id.desc()).first()

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
    analysis = get_user_analysis(user.id)
    if not analysis:
        return redirect(url_for('upload'))
    
    skills_count = len(json.loads(analysis.skills))
    missing_count = len(json.loads(analysis.missing_skills))
        
    progress = Progress.query.filter_by(user_id=user.id).first()
    completed_len = len(json.loads(progress.completed_tasks)) if progress else 3

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
    analysis = get_user_analysis(user.id)
    if not analysis: return redirect(url_for('upload'))
    
    matched = json.loads(analysis.skills)
    missing = json.loads(analysis.missing_skills)
    return render_template('skill_gap.html', user=user, analysis=analysis, matched=matched, missing=missing, active_page='skill-gap')

@app.route('/roadmap')
@login_required
def roadmap():
    user = User.query.get(session['user_id'])
    analysis = get_user_analysis(user.id)
    if not analysis: return redirect(url_for('upload'))
    
    progress = Progress.query.filter_by(user_id=user.id).first()
    
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
    analysis = get_user_analysis(user.id)
    if not analysis: return redirect(url_for('upload'))
    
    suggestions_data = []
    latest_resume = Resume.query.filter_by(user_id=user.id).order_by(Resume.id.desc()).first()
    if latest_resume:
        result = analyze_resume(latest_resume.extracted_text, analysis.role)
        suggestions_data = result['suggestions']
            
    return render_template('suggestions.html', user=user, analysis=analysis, suggestions=suggestions_data, active_page='suggestions')

@app.route('/api/download_report', methods=['GET'])
@login_required
def download_report():
    user = User.query.get(session['user_id'])
    analysis = get_user_analysis(user.id)
    if not analysis: return jsonify({'error': 'No profile mapped. Upload resume first.'}), 400
    
    from utils.report_generator import generate_pdf_report
    filepath = generate_pdf_report(analysis.score, analysis.role)
    if filepath and os.path.exists(filepath):
        return send_file(
            filepath,
            as_attachment=True,
            download_name="Skillora_Career_Report.pdf"
        )
    return jsonify({'error': 'Error generating report'}), 500
@app.route('/jobs')
@login_required
def jobs_feed():
    user = User.query.get(session['user_id'])
    
    analysis = get_user_analysis(user.id)
    if not analysis: return redirect(url_for('upload'))
    user_role = analysis.role if analysis and hasattr(analysis, 'role') and analysis.role else "software engineer"
    user_skills = set(json.loads(analysis.skills)) if analysis and hasattr(analysis, 'skills') and analysis.skills else set()
    
    # 1. Fetch Real Jobs from API
    api_jobs = fetch_real_jobs(role=user_role, limit=12)
    
    # 2. Iterate, Sync DB, Score Output
    feed_jobs = []
    for apt in api_jobs:
        job_record = Job.query.filter_by(title=apt['title'], company=apt['company']).first()
        if not job_record:
            job_record = Job(title=apt['title'], company=apt['company'], location=apt['location'], salary=apt['salary'], description=apt['description'], required_skills=apt['required_skills'], apply_link=apt.get('apply_link', ''))
            db.session.add(job_record)
            db.session.commit()
            
        req_skills = set(json.loads(job_record.required_skills)) if job_record.required_skills else set()
        matched = user_skills.intersection(req_skills)
        missing = req_skills - user_skills
        
        # Phase 3: Advanced Match Math
        skill_pct = (len(matched) / len(req_skills)) if len(req_skills) > 0 else 1
        skill_score = 0.5 * skill_pct
        role_score = 0.2 if user_role.lower() in job_record.title.lower() else 0.05
        desc_words = set(job_record.description.lower().split())
        matched_kws = user_skills.intersection(desc_words)
        kw_score = 0.2 * min((len(matched_kws) / max(len(req_skills), 1)), 1.0)
        exp_score = 0.1 # Static for now
        
        total_score = int((skill_score + role_score + kw_score + exp_score) * 100)
        total_score = min(total_score, 100)
        
        if total_score < 20: 
            continue
            
        explanation = f"You match {total_score}% because you have {', '.join(list(matched)[:3])}" if len(matched) else "You're missing core targeted skills."
        if len(missing) > 0:
            explanation += f", but lack {', '.join(list(missing)[:2])}."
        
        application = JobApplication.query.filter_by(user_id=user.id, job_id=job_record.id).first()
        saved = SavedJob.query.filter_by(user_id=user.id, job_id=job_record.id).first()
        
        feed_jobs.append({
            'job': job_record,
            'matched': list(matched),
            'missing': list(missing),
            'req_skills': list(req_skills),
            'match_score': total_score,
            'match_explanation': explanation,
            'status': application.status if application else None,
            'applied': application is not None,
            'saved': saved is not None
        })
    
    feed_jobs.sort(key=lambda x: x['match_score'], reverse=True)
    return render_template('jobs.html', user=user, feed_jobs=feed_jobs, active_page='jobs')

@app.route('/api/apply/<int:job_id>', methods=['POST'])
@login_required
def apply_job(job_id):
    user = User.query.get(session['user_id'])
    job = Job.query.get_or_404(job_id)
    
    analysis = get_user_analysis(user.id)
    if not analysis: return jsonify({'error': 'No profile mapped. Upload resume first.'}), 400
    user_skills = set(json.loads(analysis.skills)) if analysis and hasattr(analysis, 'skills') and analysis.skills else set()
    req_skills = set(json.loads(job.required_skills)) if job.required_skills else set()
    matched = user_skills.intersection(req_skills)
    match_score = int((len(matched) / len(req_skills)) * 100) if len(req_skills) > 0 else 100
    
    existing = JobApplication.query.filter_by(user_id=user.id, job_id=job.id).first()
    if not existing:
        app_record = JobApplication(user_id=user.id, job_id=job.id, match_score=match_score)
        db.session.add(app_record)
        db.session.commit()
    
    return jsonify({'success': True})

@app.route('/applications')
@login_required
def applications():
    user = User.query.get(session['user_id'])
    apps = JobApplication.query.filter_by(user_id=user.id).all()
    # Reverse timeline mock
    apps_data = []
    for a in apps:
        job = Job.query.get(a.job_id)
        apps_data.append({
            'job': job,
            'status': a.status,
            'match_score': a.match_score,
            'applied_at': a.applied_at.strftime('%B %d, %Y') if a.applied_at else "Recently"
        })
    apps_data.sort(key=lambda x: x['applied_at'], reverse=True)
    return render_template('applications.html', user=user, apps_data=apps_data, active_page='applications')

@app.route('/api/save_job/<int:job_id>', methods=['POST'])
@login_required
def save_job(job_id):
    user = User.query.get(session['user_id'])
    job = Job.query.get_or_404(job_id)
    
    existing = SavedJob.query.filter_by(user_id=user.id, job_id=job.id).first()
    if not existing:
        saved_record = SavedJob(user_id=user.id, job_id=job.id)
        db.session.add(saved_record)
        db.session.commit()
        return jsonify({'success': True, 'action': 'saved'})
    else:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'success': True, 'action': 'unsaved'})

@app.route('/saved_jobs')
@login_required
def saved_jobs():
    user = User.query.get(session['user_id'])
    analysis = get_user_analysis(user.id)
    if not analysis: return redirect(url_for('upload'))
    
    saved = SavedJob.query.filter_by(user_id=user.id).all()
    feed_jobs = []
    
    # Calculate score metrics for saved jobs iteratively
    user_skills = set(json.loads(analysis.skills)) if analysis and hasattr(analysis, 'skills') and analysis.skills else set()
    user_role = analysis.role if analysis and hasattr(analysis, 'role') and analysis.role else "software engineer"
    
    for s in saved:
        job = Job.query.get(s.job_id)
        req_skills = set(json.loads(job.required_skills)) if job.required_skills else set()
        matched = user_skills.intersection(req_skills)
        missing = req_skills - user_skills
        
        skill_pct = (len(matched) / len(req_skills)) if len(req_skills) > 0 else 1
        skill_score = 0.5 * skill_pct
        role_score = 0.2 if user_role.lower() in job.title.lower() else 0.05
        desc_words = set(job.description.lower().split())
        matched_kws = user_skills.intersection(desc_words)
        kw_score = 0.2 * min((len(matched_kws) / max(len(req_skills), 1)), 1.0)
        exp_score = 0.1 
        
        total_score = int((skill_score + role_score + kw_score + exp_score) * 100)
        total_score = min(total_score, 100)
        
        explanation = f"You match {total_score}% because you have {', '.join(list(matched)[:3])}" if len(matched) else "You're missing core targeted skills."
        if len(missing) > 0:
            explanation += f", but lack {', '.join(list(missing)[:2])}."
        
        application = JobApplication.query.filter_by(user_id=user.id, job_id=job.id).first()
        feed_jobs.append({
            'job': job,
            'matched': list(matched),
            'missing': list(missing),
            'req_skills': list(req_skills),
            'match_score': total_score,
            'match_explanation': explanation,
            'status': application.status if application else None,
            'applied': application is not None,
            'saved': True
        })
    return render_template('saved_jobs.html', user=user, feed_jobs=feed_jobs, active_page='jobs')

@app.route('/api/chat', methods=['POST'])
@login_required
def chat_bot():
    data = request.json
    msg = data.get('message', '').lower()
    history = data.get('history', [])
    
    user = User.query.get(session['user_id'])
    analysis = get_user_analysis(user.id)
    skills = analysis.skills if analysis and hasattr(analysis, 'skills') else ""
    
    from services.ai_engine import chat_response
    reply = chat_response(msg, skills, history)
         
    return jsonify({'reply': reply})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
