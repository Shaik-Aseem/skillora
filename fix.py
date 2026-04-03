import os

with open('app.py', 'r') as f:
    content = f.read()

target = "    user = User.query.get(session['user_id'])"
replacement = """    user = db.session.get(User, session.get('user_id'))
    if not user:
        session.clear()
        return redirect(url_for('login'))"""

content = content.replace(target, replacement)

with open('app.py', 'w') as f:
    f.write(content)
