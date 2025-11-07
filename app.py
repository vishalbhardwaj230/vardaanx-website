import os
import random
import smtplib
from flask import Flask, render_template, request, jsonify, redirect, url_for
from email.mime.text import MIMEText
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

# import DB setup & models
from database.db_config import db, init_db
from database.models import Student

load_dotenv()

app = Flask(__name__)
init_db(app)   # initialize SQLAlchemy here

# ==================== ROUTES ====================


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/courses')
def courses():
    return render_template('courses.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')

# Registration Route


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name").strip()
        email = request.form.get("email").strip().lower()
        password = request.form.get("password").strip()
        course = request.form.get("course").strip()

        if not name or not email or not password or not course:
            return jsonify({"error": "All fields are required!"}), 400

        existing_user = Student.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({"status": "exists", "message": "Already registered!"})

        hashed_pwd = generate_password_hash(password)
        new_student = Student(full_name=name, email=email,
                              password=hashed_pwd, course=course)
        db.session.add(new_student)
        db.session.commit()

        return jsonify({"status": "success", "redirect": url_for('student_details', email=email)})

    return render_template("register.html")


@app.route("/student-details/<email>")
def student_details(email):
    student = Student.query.filter_by(email=email).first()
    if not student:
        return "<h3 style='color:red;text-align:center;margin-top:30vh;'> Student not found</h3>"
    return render_template("student_details.html", student=student)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email").strip().lower()
        password = request.form.get("password").strip()

        student = Student.query.filter_by(email=email).first()
        if student and check_password_hash(student.password, password):
            # instead of redirect(), send JSON so JS can handle
            return jsonify({"status": "success", "redirect": url_for('student_details', email=email)})

        return jsonify({"status": "error", "message": "Invalid credentials"})
    return render_template("login.html")


# OTP SYSTEM – unchanged below
OTP_STORE = {}
ADMIN_EMAIL = os.getenv("GMAIL_ID")


@app.route('/send-otp', methods=['POST'])
def send_otp():
    data = request.get_json()
    email = data.get('email')
    otp = str(random.randint(100000, 999999))
    OTP_STORE[email] = otp

    msg = MIMEText(f"Your OTP for VardaanX contact verification is: {otp}")
    msg['Subject'] = "VardaanX OTP Verification"
    msg['From'] = ADMIN_EMAIL
    msg['To'] = email

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(ADMIN_EMAIL, os.getenv("GMAIL_APP_PASSWORD"))
            server.send_message(msg)
        return jsonify({'message': 'OTP sent to your email '})
    except Exception as e:
        print(e)
        return jsonify({'message': 'Error sending OTP'}), 500


@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    name = request.form.get('name')
    email = request.form.get('email')
    contact = request.form.get('contact')
    message = request.form.get('message')
    otp_entered = request.form.get('otp')

    if not contact:
        return "<h3 style='color:red'> Contact number missing! Please fill again.</h3>"

    full_message = f"""
    New contact submission from VardaanX website:

    Name: {name}
    Email: {email}
    Contact: {contact}
    Message: {message}
    """

    msg = MIMEText(full_message)
    msg['Subject'] = "New VardaanX Inquiry"
    msg['From'] = ADMIN_EMAIL
    msg['To'] = ADMIN_EMAIL

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(ADMIN_EMAIL, os.getenv("GMAIL_APP_PASSWORD"))
        server.send_message(msg)

    OTP_STORE.pop(email, None)
    return "<h3 style='color:green'> Your message has been sent successfully! We'll contact you soon.</h3>"


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
