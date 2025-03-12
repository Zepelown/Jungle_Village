from flask import Blueprint, render_template, request, redirect, url_for, flash
from bson.objectid import ObjectId
from create_app import mongo

bp = Blueprint("articles", __name__)

# db 객체를 인자로 받아서 사용하는 방식
articles_collection = mongo.db.articles
users_collection = mongo.db.users
comments_collection = mongo.db.comments


@bp.route("/")
def index():
    query = request.args.get("q", "").strip()  # 검색어 가져오기
    category = request.args.get("category", "").strip()  # 선택한 카테고리 가져오기
    
    # 검색 필터 생성
    search_filter = {}

    # 검색어 필터 추가
    if query:
        search_filter["$or"] = [
            {"title": {"$regex": query, "$options": "i"}},  # 제목 검색
            {"content": {"$regex": query, "$options": "i"}}  # 내용 검색
        ]

    # 카테고리 필터 추가 (전체 선택 시 필터링하지 않음)
    if category and category != "전체":
        search_filter["category"] = category

    # 필터링된 게시글 가져오기
    articles = list(articles_collection.find(search_filter))

    # 작성자 정보 추가
    for article in articles:
        user = users_collection.find_one({"_id": ObjectId(article['user_id'])})
        article['user'] = user

    return render_template("index.html", articles=articles, query=query, category=category)


@bp.route("/<article_id>")
def article_detail(article_id):
    article = articles_collection.find_one({"_id": ObjectId(article_id)})
    if not article:
        flash("게시글을 찾을 수 없습니다.", "danger")
        return redirect(url_for("articles.index"))
    
    user = users_collection.find_one({"_id": ObjectId(article['user_id'])})
    comments = list(comments_collection.find({"article_id": article_id}))
    
    for comment in comments:
        comment['user_info'] = users_collection.find_one({"_id": ObjectId(comment['user_id'])})
        for reply in comment.get('replies', []):
            reply['user_info'] = users_collection.find_one({"_id": ObjectId(reply['user_id'])})
    
    print(comments)
    
    return render_template("article_detail.html", article=article, user=user, comments=comments)

@bp.route("/write")
def write():
    nickname="정글러"
    profile_img = None
    return render_template('article_write.html', nickname=nickname, profile_img=profile_img)

@bp.route("/mypage")
def mypage():
    return render_template('mypage.html')