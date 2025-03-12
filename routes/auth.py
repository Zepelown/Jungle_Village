from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from bson.objectid import ObjectId
from create_app import mongo, SECRET_KEY
from create_app import mail
from flask_mail import Mail, Message
import jwt
import hashlib
import requests
import datetime
import random


bp = Blueprint("auth", __name__)

otp_store = {}

db = mongo.db
user_from_db = mongo.db.users

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

@bp.route("/qna")
def load_qna():
    return render_template("qna.html")

@bp.route("/send_question", methods=["POST"])
def send_question():
    contact = request.form['user_contact']
    title = request.form['question_title']
    content = request.form['question_content']
    tag = request.form['msg_tag']

    msg_title = tag + ' ' + title
    msg_body = content + '\nContact: ' + contact


    msg = Message(msg_title, sender='jungle.8.306.5@gmail.com', recipients=['jungle.8.306.5@gmail.com'])
    msg.body = msg_body

    try:
        mail.send(msg)
        return jsonify({"success": True, "message": "Email sent successfully!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@bp.route("/send_otp", methods=['POST'])
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

@bp.route('/verify_otp', methods=['POST'])
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


@bp.route("/main")
def main():
    token = request.cookies.get("jwt")

    if token and verify_token(token):
        return render_template("index.html", message="Hello, Flask with MongoDB!")
    else:
        return redirect(url_for("auth.log_in"))

@bp.route("/find_user_by_token", methods=['GET', 'POST'])
def find_user_by_token():
    token = request.cookies.get("jwt")

    if token and verify_token(token):
        result = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = result.get("email")

        user = db.users.find_one({"email": email}, {"password": 0})  # 비밀번호 제외하고 조회

        if user:
            user["_id"] = str(user["_id"])  # ObjectId를 문자열로 변환
            return jsonify(user)
        
    return jsonify({'error':"Can't find User"})
    

@bp.route("/log_in")
def log_in():
    return render_template("sign_in.html")

@bp.route("/sign_in", methods=['POST'])
def sign_in():
    email = request.form['user_email']
    pw = request.form['user_password']

    result = user_from_db.find_one({"email":email, "password":pw})

    if result:
        token = jwt.encode(
            {"email": email, "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=15)},
            SECRET_KEY,
            algorithm="HS256"
        )
        response = jsonify({"message": "로그인 성공"})
        response.set_cookie("jwt", token, httponly=True)
        return response
    else:
        return jsonify({"message": "로그인 실패"})




@bp.route("/sign_up")
def sign_up():
    return render_template("sign_up.html")

@bp.route("/complete_sign_up", methods=['POST'])
def complete_sign_up():
    email = request.form['user_email']
    password = request.form['user_password']
    nickname = request.form['user_nickname']
    generation = request.form['user_generation']

    user = {"email": email, "password": password, "nickname": nickname, "generation": generation}
    db.users.insert_one(user)

    return jsonify({'result': "success"})

@bp.route("/log_out", methods=["GET"])
def log_out():
    response = redirect(url_for("auth.log_in"))  # 로그인 페이지로 리다이렉트
    response.set_cookie("jwt", "", expires=0, max_age=0, path='/')  # 쿠키 삭제
    return response

@bp.route("/find_pw")
def find_pw():
    return render_template("find_pw.html")

@bp.route("/set_pw", methods=["POST"])
def set_pw():
    email = request.form['user_email']
    new_password = request.form['new_password']

    db.users.update_one({"email": email}, {"$set": {"password": new_password}})
    return jsonify({"message": "비밀번호 변경 성공"})

@bp.route("/check_email", methods=["POST"])
def check_email():
    email = request.form['user_email']

    result = db.users.find_one({"email":email})
    if result:
        response = jsonify({"message": "중복 이메일입니다.", "check": "false"})
        return response
    else:
        response = jsonify({"message": "사용 가능 이메일입니다.", "check": "true"})
        return response
    
@bp.route("/check_nickname", methods=["POST"])
def check_nickname():
    nickname = request.form['user_nickname']

    result = db.users.find_one({"nickname":nickname})
    if result:
        response = jsonify({"message": "중복 닉네임입니다.", "check": "false"})
        return response
    else:
        response = jsonify({"message": "사용 가능 닉네임입니다.", "check": "true"})
        return response

@bp.route("/mypage")
def mypage():
    token = request.cookies.get("jwt")

    if token and verify_token(token):
        return render_template("mypage.html")
    else:
        return redirect(url_for("auth.log_in"))
    

@bp.route("/set_nickname", methods=['POST'])
def set_nickname():
    user_email = request.form['user_email']
    new_nickname = request.form['new_nickname']
    db.users.update_one({"email": user_email}, {"$set": {"nickname": new_nickname}})

    return jsonify({"message": "닉네임 변경 성공"})

@bp.route("/set_password", methods=['POST'])
def set_password():
    user_email = request.form['user_email']
    new_password = request.form['new_password']
    db.users.update_one({"email": user_email}, {"$set": {"password": new_password}})
    
    return jsonify({"message": "닉네임 변경 성공"})

