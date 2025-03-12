from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from bson.objectid import ObjectId
from create_app import mongo, SECRET_KEY
import jwt
import hashlib
import requests
import datetime
import random
import os
from datetime import datetime

bp = Blueprint("articles", __name__)

# db 객체를 인자로 받아서 사용하는 방식
articles_collection = mongo.db.articles
users_collection = mongo.db.users
comments_collection = mongo.db.comments

def get_auth_url():
    return f"{request.host_url}auth/find_user_by_token"

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
        return redirect(url_for("auth.log_in")), jsonify({"error": "토큰이 만료되어 재로그인을 해주세요."})
    
    user_data = auth_response.json()
    return user_data
    

UPLOAD_FOLDER = 'static/article_image'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



@bp.route("/")
def index():
    token = request.cookies.get("jwt")

    if not (token and verify_token(token)):
        return redirect(url_for("auth.log_in"))
    query = request.args.get("q", "").strip()  # 검색어 가져오기
    category = request.args.get("category", "").strip()  # 선택한 카테고리 가져오기

    # 검색 필터 생성
    search_filter = {}

    # 검색어 필터 추가
    if query:
        search_filter["$or"] = [
            {"title": {"$regex": query, "$options": "i"}},  # 제목 검색
            {"content": {"$regex": query, "$options": "i"}},  # 내용 검색
        ]

    # 카테고리 필터 추가 (전체 선택 시 필터링하지 않음)
    if category and category != "전체":
        search_filter["category"] = category

    # 필터링된 게시글 가져오기
    articles = list(articles_collection.find(search_filter))

    # 작성자 정보 추가
    for article in articles:
        user = users_collection.find_one({"_id": ObjectId(article["user_id"])})
        article["user"] = user

    return render_template(
        "index.html", articles=articles, query=query, category=category
    )


@bp.route("/<article_id>")
def article_detail(article_id):
    token = request.cookies.get("jwt")
    if not (token and verify_token(token)):
        return redirect(url_for("auth.log_in"))
    
    article = articles_collection.find_one({"_id": ObjectId(article_id)})
    if not article:
        flash("게시글을 찾을 수 없습니다.", "danger")
        return redirect(url_for("articles.index"))
    

    user = users_collection.find_one({"_id": ObjectId(article["user_id"])})
    comments = list(
        comments_collection.find(
            {"article_id": article_id},
            {"_id": 1, "user_id": 1, "content": 1, "replies": 1},
        )
    )

    for comment in comments:
        comment["user_info"] = users_collection.find_one(
            {"_id": ObjectId(comment["user_id"])},
            {"nickname": 1, "generation": 1, "profile_image": 1},
        )
        for reply in comment.get("replies", []):
            reply["user_info"] = users_collection.find_one(
                {"_id": ObjectId(reply["user_id"])},
                {"nickname": 1, "generation": 1, "profile_image": 1},
            )
    total_comments = len(comments)
    total_comments += sum(len(comment.get('replies', [])) for comment in comments)

    return render_template(
        "article_detail.html", article=article, user=user, comments=comments, total_comments=total_comments
    )


@bp.route("/reply", methods=["POST"])
def reply():
    try:
        user_data = get_user_data_by_token()
        user_id = user_data.get("_id")  # ObjectId 문자열
        
        data = request.json
        comment_id = data.get("comment_id")
        content = data.get("content")

        if not comment_id or not user_id or not content:
            return jsonify({"error": "필수 데이터가 누락되었습니다."}), 400

        # 사용자 정보 조회
        user = users_collection.find_one(
            {"_id": ObjectId(user_id)},
            {"nickname": 1, "generation": 1, "profile_image": 1},
        )

        if not user:
            return jsonify({"error": "사용자를 찾을 수 없습니다."}), 404

        reply = {
            "_id": ObjectId(),
            "user_id": user_id,
            "content": content,
        }

        # 해당 댓글에 대댓글 추가
        comments_collection.update_one(
            {"_id": ObjectId(comment_id)}, {"$push": {"replies": reply}}
        )

        return jsonify(
            {
                "message": "답글이 성공적으로 추가되었습니다.",
                "reply": {
                    "content": reply["content"],
                },
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/reply", methods=["DELETE"])
def delete_reply():
    try:
        user_data = get_user_data_by_token()
        user_id = user_data.get("_id")  # ObjectId 문자열
        
        data = request.json
        comment_id = data.get("comment_id")  # 댓글 ID
        reply_id = data.get("reply_id")  # 삭제할 대댓글 ID

        if not comment_id or not reply_id or not user_id:
            return jsonify({"error": "필수 데이터가 누락되었습니다."}), 400, redirect(url_for("auth.log_in"))

        # 해당 댓글을 찾아서 대댓글이 존재하는지 확인
        comment = comments_collection.find_one({"_id": ObjectId(comment_id)})

        if not comment:
            return jsonify({"error": "댓글을 찾을 수 없습니다."}), 404

        # 대댓글이 존재하는지 확인
        reply = next((r for r in comment.get("replies", []) if str(r["_id"]) == reply_id), None)

        if not reply:
            return jsonify({"error": "대댓글을 찾을 수 없습니다."}), 404

        # 대댓글이 요청한 사용자에 의해 작성되었는지 확인
        if reply["user_id"] != user_id:
            return jsonify({"error": "이 대댓글은 사용자가 작성한 것이 아닙니다."}), 403

        # 대댓글 삭제
        comments_collection.update_one(
            {"_id": ObjectId(comment_id)},
            {"$pull": {"replies": {"_id": ObjectId(reply_id)}}}
        )

        return jsonify({"message": "대댓글이 성공적으로 삭제되었습니다."})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/comment", methods=["POST"])
def comment():
    try:
        user_data = get_user_data_by_token()
        user_id = user_data.get("_id")  # ObjectId 문자열
        
        data = request.json
        article_id = data.get("article_id")
        content = data.get("content")

        if not user_id or not content:
            return jsonify({"error": "필수 데이터가 누락되었습니다."}), 400

        comment = {
            "_id": ObjectId(),
            "content": content,
            "article_id": article_id,
            "user_id": user_id,
        }

        # 해당 댓글에 대댓글 추가
        comments_collection.insert_one(comment)

        return jsonify(
            {
                "message": "댓글이 성공적으로 추가되었습니다.",
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@bp.route("/comment", methods=["DELETE"])
def delete_comment():
    try:
        user_data = get_user_data_by_token()
        user_id = user_data.get("_id")  # ObjectId 문자열
        data = request.json
        comment_id = data.get("comment_id")

        if not user_id or not comment_id:
            return jsonify({"error": "필수 데이터가 누락되었습니다."}), 400
        # 해당 댓글에 대댓글 추가
        
        comments_collection.delete_one({"_id": ObjectId(comment_id), "user_id": user_id})
        return jsonify(
            {
                "message": "댓글이 성공적으로 삭제되었습니다.",
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@bp.route("/write", methods=["GET", "POST"])
def write():
    if request.method == "POST":
        category = request.form.get("category")
        title = request.form.get("title")
        content = request.form.get("content")
        user_data = get_user_data_by_token()
        user_id = user_data.get("_id")  # ObjectId 문자열
        date = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        image_files = request.files.getlist('image')
        image_paths = []

        #먼저 데이터 저장
        article_data = {
            "title": title,
            "content": content,
            "user_id": user_id,
            "date": date,
            "category": category,
            "images": image_paths  #빈 리스트
        }

        result = articles_collection.insert_one(article_data)

        if result:
            article_id = result.inserted_id
            user_folder = os.path.join(UPLOAD_FOLDER, user_id)
            os.makedirs(user_folder, exist_ok=True)

            for idx, image_file in enumerate(image_files):
                if image_file and allowed_file(image_file.filename):
                    filename = f"image{idx + 1}.{image_file.filename.rsplit('.', 1)[1].lower()}"
                    filepath = os.path.join(user_folder, filename)
                    image_file.save(filepath)

                    image_paths.append(f"/static/article_image/{article_id}/{filename}")
       
        articles_collection.update_one(
            {"_id": article_id},
            {"$set": {"images": image_paths}}
        )
       
        return redirect(url_for("articles.index"))
           
    return render_template("write.html")
