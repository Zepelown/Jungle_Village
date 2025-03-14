from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, g
from bson.objectid import ObjectId
from create_app import mongo, SECRET_KEY
from create_app import mail
from flask_mail import Mail, Message
import jwt
import hashlib
import requests
from datetime import datetime, timedelta
import random
import pytz
import os

bp = Blueprint("auth", __name__)

otp_store = {}

db = mongo.db
user_from_db = mongo.db.users

def get_auth_url():
    return f"{request.host_url}auth/find_user_by_token"

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
    
def get_user_data_by_token():
    auth_response = auth_response = requests.get(get_auth_url(), cookies=request.cookies)
        
    if auth_response.status_code != 200:
        return None
    
    user_data = auth_response.json()
    return user_data

UPLOAD_FOLDER = 'static/profile_image'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route("/qna")
def load_qna():
    return render_template("qna.html")


@bp.route("/send_question", methods=["POST"])
def send_question():
    contact = request.form["user_contact"]
    title = request.form["question_title"]
    content = request.form["question_content"]
    tag = request.form["msg_tag"]

    msg_title = tag + " " + title
    msg_body = content + "\nContact: " + contact

    msg = Message(
        msg_title,
        sender="jungle.8.306.5@gmail.com",
        recipients=["jungle.8.306.5@gmail.com"],
    )
    msg.body = msg_body

    try:
        mail.send(msg)
        return jsonify({"success": True, "message": "Email sent successfully!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@bp.route("/send_otp", methods=["POST"])
def send_otp():
    email = request.form["user_email"]

    if email in otp_store:
        del otp_store[email]

    new_otp = generate_otp()


    kst = pytz.timezone("Asia/Seoul")
    kst_now = datetime.now(kst)  # 현재 KST 시간
    expires_at = kst_now + timedelta(minutes=5)  # timedelta 사용


    otp_store[email] = {"otp": new_otp, "expires": expires_at}

    msg = Message(
        "이메일 인증번호", sender="jungle.8.306.5@gmail.com", recipients=[email]
    )
    msg.body = f"인증번호: {new_otp}\n5분 내로 입력하세요."
    mail.send(msg)

    return jsonify({"message": "인증번호가 이메일로 전송되었습니다."})


@bp.route("/verify_otp", methods=["POST"])
def verify_otp():
    email = request.form["user_email"]
    user_otp = request.form["user_otp"]
    
    print(otp_store)


    if email not in otp_store:
        return jsonify({"message": "인증번호가 발급되지 않았습니다.", "check": "false"})

    otp_data = otp_store[email]
    

    kst = pytz.timezone("Asia/Seoul")
    kst_now = datetime.now(kst)  # 현재 KST 시간

    if kst_now > otp_data["expires"]:
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


@bp.route("/find_user_by_token", methods=["GET", "POST"])
def find_user_by_token():
    token = request.cookies.get("jwt")

    if token and verify_token(token):
        result = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = result.get("email")

        user = db.users.find_one(
            {"email": email}, {"password": 0}
        )  # 비밀번호 제외하고 조회

        if user:
            user["_id"] = str(user["_id"])  # ObjectId를 문자열로 변환
            return jsonify(user)

    return jsonify({"error": "Can't find User"})


@bp.route("/log_in")
def log_in():
    return render_template("sign_in.html")


@bp.route("/sign_in", methods=["POST"])
def sign_in():
    email = request.form["user_email"]
    pw = request.form["user_password"]

    result = user_from_db.find_one({"email": email, "password": pw})
    
    kst = pytz.timezone("Asia/Seoul")
    kst_now = datetime.now(kst)  # 현재 KST 시간
    expires_at = kst_now + timedelta(minutes=5)  # timedelta 사용

    if result:
        token = jwt.encode(
            {
                "email": email,
                "exp": expires_at,
            },
            SECRET_KEY,
            algorithm="HS256",
        )
        response = jsonify({"message": "로그인 성공"})
        response.set_cookie("jwt", token, httponly=True)
        return response
    else:
        return jsonify({"message": "로그인 실패"})


@bp.route("/sign_up")
def sign_up():
    return render_template("sign_up.html")


@bp.route("/complete_sign_up", methods=["POST"])
def complete_sign_up():
    email = request.form["user_email"]
    password = request.form["user_password"]
    nickname = request.form["user_nickname"]
    generation = request.form["user_generation"]

    user = {
        "email": email,
        "password": password,
        "nickname": nickname,
        "generation": generation,
        "profile_image": url_for("static", filename="default_img.png", _external=True)
    }
    db.users.insert_one(user)

    return jsonify({"result": "success"})


@bp.route("/log_out", methods=["GET"])
def log_out():
    response = redirect(url_for("auth.log_in"))  # 로그인 페이지로 리다이렉트
    response.set_cookie("jwt", "", expires=0, max_age=0, path="/")  # 쿠키 삭제
    return response


@bp.route("/find_pw")
def find_pw():
    return render_template("find_pw.html")


@bp.route("/set_pw", methods=["POST"])
def set_pw():
    email = request.form["user_email"]
    new_password = request.form["new_password"]

    db.users.update_one({"email": email}, {"$set": {"password": new_password}})
    return jsonify({"message": "비밀번호 변경 성공"})


@bp.route("/check_email", methods=["POST"])
def check_email():
    email = request.form["user_email"]

    result = db.users.find_one({"email": email})
    if result:
        response = jsonify({"message": "중복 이메일입니다.", "check": "false"})
        return response
    else:
        response = jsonify({"message": "사용 가능 이메일입니다.", "check": "true"})
        return response


@bp.route("/check_nickname", methods=["POST"])
def check_nickname():
    nickname = request.form["user_nickname"]

    result = db.users.find_one({"nickname": nickname})
    if result:
        response = jsonify({"message": "중복 닉네임입니다.", "check": "false"})
        return response
    else:
        response = jsonify({"message": "사용 가능 닉네임입니다.", "check": "true"})
        return response

@bp.route("/update_profile_image", methods=["POST"])
def update_profile_image():
    user_data = get_user_data_by_token()
    user_id = user_data.get("_id")
    file = request.files.get('profile_image')

    if not file or not allowed_file(file.filename):
        return jsonify({"message": "유효한 이미지 파일('jpg', 'jpeg', 'png')형식으로 업로드 해주세요.", "status": "error"})

    file_extension = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{user_id}.{file_extension}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    db.users.update_one(
        {"_id": ObjectId(user_id)}, 
        {"$set": {"profile_image": f"/static/profile_image/{filename}"}}
    )

    return jsonify({"message": "프로필 사진이 변경되었습니다", "status": "success"})

@bp.route("/update_nickname", methods=["POST"])
def update_nickname():
    user_data = get_user_data_by_token()
    user_id = user_data.get("_id")
    new_nickname = request.form['user_nickname']

    # 닉네임 중복 체크
    existing_user = db.users.find_one({"nickname": new_nickname})
    if existing_user:
        return jsonify({"message": "중복된 닉네임입니다.", "status": "error"})

    # MongoDB에서 닉네임 업데이트
    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"nickname": new_nickname}}
    )

    return jsonify({"message": "닉네임이 성공적으로 변경되었습니다", "status": "success"})

@bp.route("/update_password", methods=["POST"])
def update_password():
    user_data = get_user_data_by_token()
    user_id = user_data.get("_id")
    new_password = request.form['password']

    # 비밀번호 변경
    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"password": new_password}}
    )

    # 성공적인 비밀번호 변경 후 응답
    return jsonify({"message": "비밀번호가 성공적으로 변경되었습니다.", "status": "success"})