import re
import json
from services.ai_engine import analyze_resume_text, suggest_improvements

def score_job_match(job_record, user_skills, user_role):
    req_skills = set(json.loads(job_record.required_skills)) if job_record.required_skills else set()
    matched = user_skills.intersection(req_skills)
    missing = req_skills - user_skills
    
    skill_pct = (len(matched) / len(req_skills)) if len(req_skills) > 0 else 1
    skill_score = 0.5 * skill_pct
    role_score = 0.2 if user_role and user_role.lower() in job_record.title.lower() else 0.05
    desc_words = set(job_record.description.lower().split())
    matched_kws = user_skills.intersection(desc_words)
    kw_score = 0.2 * min((len(matched_kws) / max(len(req_skills), 1)), 1.0)
    exp_score = 0.1 
    
    total_score = int((skill_score + role_score + kw_score + exp_score) * 100)
    total_score = min(total_score, 100)
    
    # Advanced metrics
    readiness_score = min(int(total_score * 0.85 + 10), 100)
    ats_probability = min(total_score + 5, 99)
    
    explanation = f"You match {total_score}% because you have {', '.join(list(matched)[:3])}" if len(matched) else "You're missing core targeted skills."
    if len(missing) > 0:
        explanation += f", but lack {', '.join(list(missing)[:2])}."
        
    why_apply = ""
    if total_score >= 80:
        why_apply = f"Your background in {list(matched)[0] if matched else user_role} gives you a competitive tier-1 edge."
    elif total_score >= 50:
        why_apply = "You meet foundational requirements. A strong cover letter could secure an interview."
    else:
        why_apply = "This role overlaps with your profile loosely."

    return {
        'total_score': total_score,
        'readiness_score': readiness_score,
        'ats_probability': ats_probability,
        'explanation': explanation,
        'why_apply': why_apply,
        'matched': list(matched),
        'missing': list(missing),
        'req_skills': list(req_skills)
    }

ROLES = {
    'Software Engineer': {
        'skills': ['python', 'java', 'javascript', 'react', 'node', 'sql', 'git', 'docker', 'aws', 'api', 'flask', 'django', 'html', 'css', 'agile', 'linux'],
    },
    'Data Analyst': {
        'skills': ['sql', 'excel', 'python', 'tableau', 'power bi', 'statistics', 'r', 'data visualization', 'modeling', 'pandas', 'numpy', 'machine learning', 'dashboard'],
    },
    'AIML Engineer': {
        'skills': ['python', 'tensorflow', 'pytorch', 'machine learning', 'deep learning', 'nlp', 'computer vision', 'sql', 'docker', 'kubernetes', 'aws', 'gcp', 'scikit-learn', 'pandas']
    }
}

def analyze_resume(text, role):
    text_lower = text.lower()
    
    # 1. Use Gemini for dynamic parsing
    ai_data = analyze_resume_text(text)
    
    target_skills = ROLES.get(role, ROLES['Software Engineer'])['skills'].copy()
    
    # Blend AI skills into targeted skills logic
    dynamic_skills = set([s.lower() for s in ai_data.get('skills', [])])
    for s in dynamic_skills:
        if s not in target_skills:
            target_skills.append(s)
            
    found_skills = []
    missing_skills = []
    
    for skill in target_skills:
        if re.search(r'\b' + re.escape(skill) + r'\b', text_lower) or re.search(r'\b' + re.escape(skill.replace(' ', '')) + r'\b', text_lower):
            found_skills.append(skill.upper() if len(skill) <= 3 else skill.title())
        else:
            missing_skills.append(skill.upper() if len(skill) <= 3 else skill.title())
            
    score = int((len(found_skills) / len(target_skills)) * 100) if target_skills else 0
    score = min(score + 10, 95)
    
    # 2. Use AI for deep text-based suggestions
    ai_suggestions = suggest_improvements(text)
    
    roadmaps = []
    if missing_skills:
        roadmaps.append({
            'week': 'Week 1-2',
            'title': 'Core missing skills',
            'tasks': [f"Learn {skill}" for skill in missing_skills[:3]]
        })
        if len(missing_skills) > 3:
            roadmaps.append({
                'week': 'Week 3-4',
                'title': 'Advanced mechanics',
                'tasks': [f"Learn {skill}" for skill in missing_skills[3:6]]
            })
            
    return {
        'score': score,
        'breakdown': {
            'skills_match': score,
            'keywords': min(score + 15, 100),
            'experience': min(score + 20, 100) if score > 50 else 40,
            'formatting': 85
        },
        'found_skills': list(set(found_skills)),
        'missing_skills': list(set(missing_skills)),
        'roadmap': roadmaps,
        'suggestions': ai_suggestions
    }
