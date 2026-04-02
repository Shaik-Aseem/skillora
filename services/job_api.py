import requests
import json
import re

def clean_html(raw_html):
    if not raw_html:
        return ""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', str(raw_html))
    # Replace multiple spaces with single space
    cleantext = re.sub(r'\s+', ' ', cleantext).strip()
    return cleantext[:400] + "..." if len(cleantext) > 400 else cleantext

def fetch_real_jobs(role="software engineer", limit=10):
    url = f"https://remotive.com/api/remote-jobs?search={role}&limit={limit}"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        jobs_list = data.get("jobs", [])
        if not jobs_list:
            url = f"https://remotive.com/api/remote-jobs?category=software-dev&limit={limit}"
            res = requests.get(url, timeout=5)
            res.raise_for_status()
            jobs_list = res.json().get("jobs", [])
            
        normalized_jobs = []
        for job in jobs_list[:limit]:
            title = job.get('title', 'Software Engineer')
            company = job.get('company_name', 'Tech Company')
            location = job.get('candidate_required_location', 'Remote')
            salary = job.get('salary', '') or 'Competitive'
            desc = clean_html(job.get('description', ''))
            
            tags = job.get('tags', [])
            skills = tags if tags else [role, "Teamwork", "Agile"]
            
            normalized_jobs.append({
                "title": title,
                "company": company,
                "location": location,
                "salary": salary,
                "description": desc,
                "required_skills": json.dumps(skills),
                "apply_link": job.get('url', '')
            })
        return normalized_jobs
    except Exception as e:
        print(f"[Job API Error] {e}")
        return _get_mock_jobs()

def _get_mock_jobs():
    return [
        {"title": "Software Engineer", "company": "TechNova", "location": "Remote", "salary": "$120k", "description": "Looking for a Python/React developer.", "required_skills": '["Python", "React", "SQL"]', "apply_link": "#"},
        {"title": "Machine Learning Engineer", "company": "AI Dynamics", "location": "New York, NY", "salary": "$150k", "description": "Build predictive models.", "required_skills": '["Python", "Machine Learning", "TensorFlow", "SQL"]', "apply_link": "#"},
        {"title": "Data Analyst", "company": "FinData", "location": "Chicago, IL", "salary": "$90k", "description": "Analyze financial data trends.", "required_skills": '["SQL", "Python", "Tableau", "Excel"]', "apply_link": "#"}
    ]
