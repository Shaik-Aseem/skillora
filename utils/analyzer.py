import re

# Mock roles for skill gap
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
    
    target_skills = ROLES.get(role, ROLES['Software Engineer'])['skills']
    
    found_skills = []
    missing_skills = []
    
    for skill in target_skills:
        # Simple word boundary regex search
        if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
            found_skills.append(skill.title())
        elif re.search(r'\b' + re.escape(skill.replace(' ', '')) + r'\b', text_lower):
            found_skills.append(skill.title())
        else:
            missing_skills.append(skill.title())
            
    # Calculate score
    score = int((len(found_skills) / len(target_skills)) * 100) if target_skills else 0
    score = min(score + 10, 95) # Boost mock score slightly for demo purposes
    
    # Mock projects/education detection simply by checking for keywords
    has_education = any(word in text_lower for word in ['education', 'university', 'college', 'degree', 'bachelor', 'master'])
    has_projects = any(word in text_lower for word in ['project', 'projects', 'portfolio', 'github'])
    
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
                'title': 'Advanced skills',
                'tasks': [f"Learn {skill}" for skill in missing_skills[3:6]]
            })
            
    suggestions = []
    if not has_education:
        suggestions.append("Add a clear Education section with your degree and university.")
    if not has_projects:
        suggestions.append("Add a Projects section highlighting relevant technical projects.")
    
    if score < 50:
        suggestions.append(f"Consider learning core {role} skills like {', '.join(missing_skills[:3])}. Try taking an online course to get familiar with them.")
    else:
        suggestions.append("Your skills match the role fairly well! Focus on building projects highlighting these skills.")
    suggestions.append("Use strong action verbs such as 'Developed', 'Engineered', and 'Architected'.")
    
    return {
        'score': score,
        'breakdown': {
            'skills_match': score,
            'keywords': min(score + 15, 100),
            'experience': min(score + 20, 100) if has_projects else 40,
            'formatting': 85  # Hardcoded mock
        },
        'found_skills': found_skills,
        'missing_skills': missing_skills,
        'roadmap': roadmaps,
        'suggestions': suggestions
    }
