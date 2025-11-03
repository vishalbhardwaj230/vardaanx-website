import os
from flask import Flask, render_template
from flask import Flask, render_template, request, jsonify
import random
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# MS SQL connection using Windows Authentication
app.config['SQLALCHEMY_DATABASE_URI'] = (
    "mssql+pyodbc://@VISHALBHARDWAJ\\SQLEXPRESS/vardaanx_db"
    "?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)


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


OTP_STORE = {}
ADMIN_EMAIL = "bvishal284@gmail.com"   # 👈 Replace with your email


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
            server.login(ADMIN_EMAIL, "fxmf mxqm henj grny")
            server.send_message(msg)
        return jsonify({'message': 'OTP sent to your email ✅'})
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
        return "<h3 style='color:red'>❌ Contact number missing! Please fill again.</h3>"

    # Once verified → send email to you
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
        server.login(ADMIN_EMAIL, "fxmf mxqm henj grny")
        server.send_message(msg)

    OTP_STORE.pop(email, None)
    return "<h3 style='color:green'>✅ Your message has been sent successfully! We'll contact you soon.</h3>"


print("Templates folder absolute path:",
      os.path.join(os.getcwd(), "templates"))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
