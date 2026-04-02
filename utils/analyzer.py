import re
from services.ai_engine import analyze_resume_text, suggest_improvements

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
