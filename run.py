
from flask import Flask, render_template, jsonify, request, redirect, url_for
from pymongo import MongoClient
import os
from dotenv import load_dotenv

from flask_mail import Mail, Message
import jwt
import hashlib
import requests
import datetime
import random
load_dotenv()

app = Flask(__name__)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'jungle.8.306.5@gmail.com' 
app.config['MAIL_PASSWORD'] = 'jhuv srgz mtdu pryi'  
app.config['MAIL_DEFAULT_SENDER'] = 'jungle.8.306.5@gmail.com'

mail = Mail(app)
otp_store = {}


MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.get_database()

# client = MongoClient('localhost', 27017)
# db = client.testJungle
user_from_db = db.users         

#유저테이블 참조

SECRET_KEY = 'jungle_village_secret_key'

def generate_otp():
    return str(random.randint(100000, 999999))

def verify_token(token):
    try:
        result = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return result
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

@app.route("/")
def home():
    token = request.cookies.get("jwt")

    if token and verify_token(token):
        return redirect(url_for("main"))
    else:
        return redirect(url_for("log_in"))

@app.route("/qna")
def load_qna():
    return render_template("qna.html")

@app.route("/send_otp", methods=['POST'])
def send_otp():
    email = request.form['user_email']

    if email in otp_store:
        del otp_store[email]

    new_otp = generate_otp()
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)

    otp_store[email] = {"otp": new_otp, "expires": expires_at}

    msg = Message('이메일 인증번호', sender='jungle.8.306.5@gmail.com', recipients=[email])
    msg.body = f'인증번호: {new_otp}\n5분 내로 입력하세요.'
    mail.send(msg)

    return jsonify({"message": "인증번호가 이메일로 전송되었습니다."})

@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    email = request.form['user_email']
    user_otp = request.form['user_otp']

    if email not in otp_store:
        return jsonify({"message": "인증번호가 발급되지 않았습니다.", "check": "false"})

    otp_data = otp_store[email]

    
    if datetime.datetime.utcnow() > otp_data["expires"]:
        return jsonify({"message": "인증번호가 만료되었습니다.", "check": "false"})

    if user_otp == otp_data["otp"]:
        del otp_store[email]  
        return jsonify({"message": "인증 성공!", "check": "true"})
    else:
        return jsonify({"message": "인증번호가 틀렸습니다.", "check": "false"})


@app.route("/main")
def main():
    token = request.cookies.get("jwt")

    if token and verify_token(token):
        return render_template("index.html", message="Hello, Flask with MongoDB!")
    else:
        return redirect(url_for("log_in"))

@app.route("/log_in")
def log_in():
    return render_template("sign_in.html")

@app.route("/sign_in", methods=['POST'])
def sign_in():
    email = request.form['user_email']
    pw = request.form['user_password']

    result = user_from_db.find_one({"email":email, "password":pw})

    if result:
        token = jwt.encode(
            {"email": email, "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=1)},
            SECRET_KEY,
            algorithm="HS256"
        )
        response = jsonify({"message": "로그인 성공"})
        response.set_cookie("jwt", token, httponly=True)
        return response
    else:
        return jsonify({"message": "로그인 실패"})




@app.route("/sign_up")
def sign_up():
    return render_template("sign_up.html")

@app.route("/complete_sign_up", methods=['POST'])
def complete_sign_up():
    email = request.form['user_email']
    password = request.form['user_password']
    nickname = request.form['user_nickname']
    generation = request.form['user_generation']

    user = {"email": email, "password": password, "nickname": nickname, "generation": generation}
    db.users.insert_one(user)

    return jsonify({'result': "success"})

@app.route("/log_out", methods=["POST"])
def log_out():
    response = jsonify({"message": "로그아웃 성공"})
    response.set_cookie("jwt", "", expires=0)  
    return response

@app.route("/find_pw")
def find_pw():
    return render_template("find_pw.html")

@app.route("/set_pw", methods=["POST"])
def set_pw():
    email = request.form['user_email']
    new_password = request.form['new_password']

    db.users.update_one({"email": email}, {"$set": {"password": new_password}})
    return jsonify({"message": "비밀번호 변경 성공"})

@app.route("/check_email", methods=["POST"])
def check_email():
    email = request.form['user_email']

    result = db.users.find_one({"email":email})
    if result:
        response = jsonify({"message": "중복 이메일입니다.", "check": "false"})
        return response
    else:
        response = jsonify({"message": "사용 가능 이메일입니다.", "check": "true"})
        return response
    
@app.route("/check_nickname", methods=["POST"])
def check_nickname():
    nickname = request.form['user_nickname']

    result = db.users.find_one({"nickname":nickname})
    if result:
        response = jsonify({"message": "중복 닉네임입니다.", "check": "false"})
        return response
    else:
        response = jsonify({"message": "사용 가능 닉네임입니다.", "check": "true"})
        return response

if __name__ == "__main__":
    app.run(debug=True)

from create_app import create_app

app = create_app()  # app.py에서 생성한 Flask 애플리케이션 인스턴스 가져오기

if __name__ == "__main__":
    app.run(debug=True)
