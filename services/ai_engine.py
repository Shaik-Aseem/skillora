import os
try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

def get_ai_response(prompt, system_instruction="You are an expert AI Career Coach."):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or not HAS_GENAI:
        return _mock_ai_response(prompt)
    
    genai.configure(api_key=api_key)
    
    # Using gemini-pro for text generation
    model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_instruction)
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"[AI Error] {e}")
        return _mock_ai_response(prompt)

def analyze_resume_text(text):
    prompt = f"Analyze the following resume and extract the main role, top 5 skills, and a brief 2-sentence summary. Format as JSON with keys: role, skills (list), summary.\n\nResume:\n{text[:2000]}"
    try:
        response = get_ai_response(prompt, "You are an ATS parsing engine. Reply ONLY in strict JSON.")
        import json
        import re
        # Clean response string to ensure JSON loads
        clean_json = re.sub(r'```json\n|```|', '', response).strip()
        data = json.loads(clean_json)
        return {"role": data.get("role", "Software Engineer"), "skills": data.get("skills", []), "summary": data.get("summary", "")}
    except Exception as e:
        print(f"[AI Parsing Error] {e}")
        return {"role": "Software Engineer", "skills": ["Python", "React", "Teamwork"], "summary": "Highly motivated candidate with strong technical foundation."}

def suggest_improvements(text):
    prompt = f"Given this resume, provide exactly 3 concise, highly actionable bullet-point suggestions to improve the resume for ATS systems.\n\nResume:\n{text[:2000]}"
    response = get_ai_response(prompt, "You are an expert resume reviewer.")
    
    # Split bullet points roughly
    points = [p.replace('*', '').strip() for p in response.split('\n') if p.strip() and ('-' in p[:3] or '*' in p[:3])]
    if len(points) >= 3:
        return points[:3]
    return [
        "Include more quantifiable metrics in your experience section (e.g., 'increased revenue by 20%').",
        "Add a technical skills section matching keywords from job descriptions perfectly.",
        "Remove passive language and replace with strong action verbs (Architected, Spearheaded)."
    ]

def chat_response(user_msg, user_skills="", history=None):
    if history is None:
        history = []
    
    # Compress last 4 messages logically
    hist_str = "\n".join([f"{m.get('sender', 'user')}: {m.get('text', '')}" for m in history[-4:]])
    prompt = f"Chat Context:\n{hist_str}\n\nUser asks: '{user_msg}'. User's known skills: {user_skills}. Answer in 2 short, helpful sentences as a career coach."
    return get_ai_response(prompt, "You are Skillora, an AI Career Coach. Be friendly, concise, and professional.")

def _mock_ai_response(prompt):
    p = prompt.lower()
    if "analyze" in p:
        return '{"role": "Software Engineer", "skills": ["Python", "Communication", "Agile"], "summary": "Great mock candidate."}'
    if "improve" in p:
        return "- Add metrics.\n- Use action verbs.\n- Tailor keywords to the job description."
    
    if "skills" in p or "learn" in p:
         return "Based on current market demand, I highly recommend expanding into modern frameworks like React and Cloud architecture (AWS/Docker)."
    elif "improve" in p or "resume" in p:
         return "Pro tip: Convert passive statements into actionable achievements. Replace 'Helped with a website' to 'Engineered a full-stack platform decreasing latency by 20%'."
    elif "rejected" in p or "not getting" in p:
         return "ATS engines act as strict keyword filters. Always match your resume's terminology exactly to the job description keywords for the highest conversion probability."
         
    return "I'm your AI Career Coach. Provide your GEMINI_API_KEY to activate dynamic generative responses!"
