from flask import Flask, render_template, request, redirect, send_file, session
import sqlite3
import pdfkit
import os
from google import genai  # Import the new Google GenAI library

app = Flask(__name__)
app.secret_key = "mysecretkey123"


os.environ["GEMINI_API_KEY"] = "AIzaSyB1xZ8bEQvP5Lh8O-S9mMvQEhz_r8dZIjA"
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")

# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (name, email, password) VALUES (?,?,?)",
                (name, email, password)
            )
            conn.commit()
        except:
            return "User already exists!"

        conn.close()
        return redirect("/login")

    return render_template("signup.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            return redirect("/dashboard")
        else:
            return "Invalid Email or Password"

    return render_template("login.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM resumes")
    resumes = cursor.fetchall()

    conn.close()
    return render_template("dashboard.html", resumes=resumes)
#--------templates--------
@app.route("/templates")
def templates():
    return render_template("templates.html")

# ---------------- AUTO GENERATE ----------------
@app.route('/auto_generate', methods=['GET', 'POST'])
def auto_generate():
    if request.method == 'POST':
        job_role = request.form.get('job_role')

        if job_role:
            job_role = job_role.lower()
        else:
            job_role = ""

        if "developer" in job_role:
            template = "chronological"
        elif "student" in job_role:
            template = "functional"
        elif "designer" in job_role:
            template = "creative"
        elif "manager" in job_role:
            template = "combination"
        else:
            template = "functional"

        return redirect(f'/form?template={template}')

    return render_template('auto_generate.html')

# ---------------- FORM ----------------
@app.route('/form')
def form():
    template = request.args.get('template') or "chronological"
    return render_template('form.html', template=template)

# ---------------- AI SUMMARY ----------------
def generate_summary(skills, degree):
    skills = skills or "general skills"
    degree = degree or "graduate"
    
    degree_lower = degree.lower()

    if "bcom" in degree_lower:
        extra = "finance, accounting, business operations"
    elif "bba" in degree_lower:
        extra = "management, leadership, marketing"
    elif "bca" in degree_lower or "mca" in degree_lower:
        extra = "software development, programming"
    else:
        extra = "professional skills"

    prompt = f"""
You are a professional HR recruiter.

Write a 3-line ATS-friendly resume summary.

Candidate Details:
Degree: {degree}
Skills: {skills}

RULES:
- Make it suitable for ANY degree (not only tech)
- Keep it professional and job-ready
- Use strong keywords for placement
- Do NOT mention "candidate" or "this person"
- Do NOT give multiple options
- Only final answer (3 lines)

Example style:
"Motivated graduate with strong analytical and problem-solving skills..."
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text.strip()

    except Exception as e:
        print("GEMINI ERROR:", e)
        return "Motivated graduate with strong skills and a passion for professional growth."
    
# ---------------- AI IMPROVEMENT ----------------
def ai_resume_improvement(skills, projects, experience):
    prompt = f"""
Improve this resume:

Skills: {skills}
Projects: {projects}
Experience: {experience}

Give ONLY 4 bullet points:
• ...
• ...
• ...
• ...
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text.strip()

    except Exception as e:
        print("AI ERROR:", e)
        return "• Add projects\n• Use action verbs\n• Add impact\n• Improve formatting" 
    
# ---------------- AI SKILLS ----------------
def ai_skill_suggestions(skills, degree):
    prompt = f"""
Suggest 3 job-ready skills.

Skills: {skills}
Degree: {degree}


Output:
Skill1, Skill2, Skill3
"""

    try:
        response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt
)
        return response.text.strip()

    except Exception as e:
        print("AI ERROR:", e)
        return "React, Node.js, MongoDB"
    
# ---------------- GENERATE RESUME ----------------
@app.route("/generate_resume", methods=["POST"])
def generate_resume():
    data = request.form.to_dict()  

    template = data.get("template") or "chronological"
    theme_color = data.get("theme_color")

    
    data.pop("template", None)
    data.pop("theme_color", None)

    # AI
    ai_summary = generate_summary(data.get("skills"), data.get("degree"))
    ai_output = ai_resume_improvement(
        data.get("skills"),
        data.get("projects"),
        data.get("experience")
    )
    ai_skills = ai_skill_suggestions(
        data.get("skills"),
        data.get("degree")
    )


    # Save session
    session["user_data"] = {
        **data,
        "template": template,
        "theme_color": theme_color,
        "ai_summary": ai_summary
    }

    return render_template(
        "resume.html",
        **data,
        template=template,
        theme_color=theme_color,
        ai_summary=ai_summary,
        ai_output=ai_output,
        ai_skills=ai_skills
    )

# ---------------- JOB LOGIC ----------------
job_skills = {
    "Frontend Developer": ["html", "css", "javascript"],
    "Python Developer": ["python", "flask", "sql"]
}

def suggest_jobs(skills, degree):
    skills = (skills or "").lower()
    degree = (degree or "").lower()
    jobs = []

    # Logic for Government/High-Paying roles based on your goals
    if "mca" in degree or "python" in skills:
        jobs.append("Software Engineer (NIC/ISRO)")
    
    if "react" in skills or "javascript" in skills:
        jobs.append("Frontend Developer")
        
    if "sql" in skills or "dbms" in skills:
        jobs.append("Database Administrator")

    return jobs if jobs else ["IT Trainee"]


# ---------------- AI ANALYSIS PAGE ----------------
@app.route("/ai_analysis")
def ai_analysis():
    data = session.get("user_data")

    if not data:
        return "No data found. Please generate resume first."

    skills = data.get("skills", "HTML, CSS, JavaScript")
    projects = data.get("projects", "No projects")
    experience = data.get("experience", "Fresher")
    degree = data.get("degree", "Graduate")

    ai_output = ai_resume_improvement(skills, projects, experience)
    ai_skills = ai_skill_suggestions(skills, degree)
    jobs = suggest_jobs(skills, degree)

    print("AI OUTPUT:", ai_output)
    print("AI SKILLS:", ai_skills)
    print("JOBS:", jobs)

    return render_template(
        "ai_analysis.html",
        ai_output=ai_output,
        ai_skills=ai_skills,
        jobs=jobs,
        suggestions=[
            "Add more projects",
            "Use strong action verbs",
            "Improve resume formatting"
        ]
    )
# ---------------- PDF ----------------
def create_pdf(data):
    data = dict(data)  # make safe copy

    template = data.get("template")
    theme_color = data.get("theme_color")

    # REMOVE duplicates
    data.pop("template", None)
    data.pop("theme_color", None)

    rendered = render_template(
        "resume.html",
        **data,
        template=template,
        theme_color=theme_color,
        pdf_mode=True
    )

    config = pdfkit.configuration(
        wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    )

    options = {
        'enable-local-file-access': None,
        'page-size': 'A4',
        'margin-top': '0mm',
        'margin-right': '0mm',
        'margin-bottom': '0mm',
        'margin-left': '0mm',
        'print-media-type': None,
        'encoding': "UTF-8"
    }

    pdfkit.from_string(
        rendered,
        "resume.pdf",
        configuration=config,
        options=options
    )

@app.route("/download")
def download():
    data = session.get("user_data")

    if not data:
        return "No resume found"

    create_pdf(data)
    return send_file("resume.pdf", as_attachment=True)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)