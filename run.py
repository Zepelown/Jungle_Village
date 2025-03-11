from flask import Flask, render_template, request, redirect, url_for, flash
from bson.objectid import ObjectId
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# MongoDB 연결 설정
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.junglevillage

articles_collection = db.articles  # 게시글 컬렉션
users_collection = db.users
comments_collection = db.comments

# # ✅ 게시글 목록
# @app.route("/")
# def index():
#     articles = list(articles_collection.find())  # 커서를 리스트로 변환
    
#     for article in articles:
#         user = users_collection.find_one({"_id": ObjectId(article['user_id'])})
#         article['user'] = user  # article에 user 정보를 추가
        
#     return render_template("index.html", articles=articles)

@app.route("/")
def index():
    query = request.args.get("q", "").strip()  # 검색어 가져오기 (없으면 빈 문자열)
    
    # 기본적으로 모든 게시글 가져오기
    search_filter = {}
    if query:
        # 제목 또는 내용에 검색어가 포함된 게시글 찾기 (대소문자 구분 없이)
        search_filter = {
            "$or": [
                {"title": {"$regex": query, "$options": "i"}},  # 제목 검색
                {"content": {"$regex": query, "$options": "i"}}  # 내용 검색
            ]
        }
    
    articles = list(articles_collection.find(search_filter))  # 필터링된 게시글 가져오기
    
    # 게시글에 user 정보 추가
    for article in articles:
        user = users_collection.find_one({"_id": ObjectId(article['user_id'])})
        article['user'] = user
    
    return render_template("index.html", articles=articles, query=query)


# ✅ 게시글 상세 보기
@app.route("/<article_id>")
def article_detail(article_id):
    article = articles_collection.find_one({"_id": ObjectId(article_id)})
    if not article:
        flash("게시글을 찾을 수 없습니다.", "danger")
        return redirect(url_for("articles_list"))
    
    user = users_collection.find_one({"_id": ObjectId(article['user_id'])})
    comments = list(comments_collection.find({"article_id" : article_id}))
    
    for comment in comments:
        comment['user_info'] = users_collection.find_one({"_id": ObjectId(comment['user_id'])})
        # 답글 작성자의 정보도 추가
        for reply in comment.get('replies', []):
            reply['user_info'] = users_collection.find_one({"_id": ObjectId(reply['user_id'])})

    return render_template("article_detail.html", article=article, user=user, comments=comments)

if __name__ == "__main__":
    app.run(debug=True)