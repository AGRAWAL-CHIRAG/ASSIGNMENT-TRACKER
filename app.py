import os
import sqlite3
import requests
import time
from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory, flash

app = Flask(__name__)
app.secret_key = "chirag_mit_pune_2026"

# --- ABSOLUTE PATHS ---
USER = "chirag8177852640"
BASE_DIR = f'/home/{USER}'
DB_PATH = os.path.join(BASE_DIR, 'deadlines.db')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

# --- CONFIGURATION ---
TOKEN = "8376663796:AAFiJaqqLc8dXKtHuQM9XAJb2LgCxvo8Y08"

STUDENT_REGISTRY = {
    "Chirag": "6427192906",
    "Manshur": "6679584959",
    "kolekar": "7247679008",
    "rose": "5114566818",
    "ritesh":"7974025227"
}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS assignments
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, deadline TEXT, priority TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS submissions
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, assignment_id INTEGER, student_name TEXT, filename TEXT)''')
    conn.commit()
    conn.close()

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    for name, chat_id in STUDENT_REGISTRY.items():
        payload = {"chat_id": chat_id, "text": f"🔔 *Hello {name}!*\n\n{message}", "parse_mode": "Markdown"}
        try:
            requests.post(url, data=payload, timeout=5)
            time.sleep(0.3)
        except: print(f"Failed to notify {name}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role, user, pw = request.form.get('role'), request.form.get('username'), request.form.get('password')
        creds = {'faculty': ('faculty_admin', 'faculty123'), 'student': ('student_user', 'student123')}
        if role in creds and user == creds[role][0] and pw == creds[role][1]:
            session['role'], session['username'] = role, user
            return redirect(url_for('dashboard'))
        flash("Invalid Username or Password!", "danger")
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'role' not in session: return redirect(url_for('login'))
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM assignments ORDER BY CASE WHEN priority='High' THEN 1 WHEN priority='Medium' THEN 2 ELSE 3 END, deadline ASC")
    tasks = cursor.fetchall()
    subs = []
    if session['role'] == 'faculty':
        cursor.execute("SELECT submissions.student_name, assignments.title, submissions.filename FROM submissions JOIN assignments ON assignments.id = submissions.assignment_id")
        subs = cursor.fetchall()
    conn.close()
    return render_template('dashboard.html', tasks=tasks, role=session['role'], submissions=subs)

@app.route('/download/<filename>')
def download_file(filename):
    if 'role' not in session or session['role'] != 'faculty': return "Unauthorized", 403
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/add_assignment', methods=['POST'])
def add_assignment():
    t, d, p = request.form.get('title'), request.form.get('date'), request.form.get('priority')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO assignments (title, deadline, priority) VALUES (?, ?, ?)", (t, d, p))
    conn.commit()
    conn.close()
    send_telegram(f"📢 *NEW ASSIGNMENT*\n📌 *{t}*\n🔥 Priority: {p}\n📅 Due: {d}")
    flash("Assignment Posted Successfully & Notifications Sent!", "success")
    return redirect(url_for('dashboard'))

@app.route('/upload/<int:tid>', methods=['POST'])
def upload(tid):
    f = request.files['file']
    if f:
        fname = f"{session['username']}_{f.filename}"
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO submissions (assignment_id, student_name, filename) VALUES (?, ?, ?)", (tid, session['username'], fname))
        conn.commit()
        conn.close()
        flash("File Uploaded Successfully!", "success")
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)