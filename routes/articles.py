from flask import Blueprint, render_template, request, redirect, url_for, flash
import os
from datetime import datetime
from create_app import mongo
from bson.objectid import ObjectId

bp = Blueprint("articles", __name__)

# db 객체를 인자로 받아서 사용하는 방식
articles_collection = mongo.db.articles
users_collection = mongo.db.users
comments_collection = mongo.db.comments

UPLOAD_FOLDER = 'static/article_image'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_current_user_id():
    #추후에 사용자 ID를 가져오는 로직으로 변경해야함 (현재는 더미 데이터)
    return "67cfb44b8c8918f658c51832"

@bp.route("/")
def index():
    query = request.args.get("q", "").strip()  # 검색어 가져오기
    
    # 기본적으로 모든 게시글 가져오기
    search_filter = {}
    if query:
        search_filter = {
            "$or": [
                {"title": {"$regex": query, "$options": "i"}},  # 제목 검색
                {"content": {"$regex": query, "$options": "i"}}  # 내용 검색
            ]
        }
    
    articles = list(articles_collection.find(search_filter))  # 필터링된 게시글 가져오기
    
    for article in articles:
        user = users_collection.find_one({"_id": ObjectId(article['user_id'])})
        article['user'] = user
    
    return render_template("index.html", articles=articles, query=query)

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
    
    return render_template("article_detail.html", article=article, user=user, comments=comments)


@bp.route("/write", methods=["GET", "POST"])
def write():
    if request.method == "POST":
        category = request.form.get("category")
        title = request.form.get("title")
        content = request.form.get("content")
        user_id = get_current_user_id()
        date = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        image_files = request.files.getlist('image')
        image_paths = []

        if image_files:
            user_folder = os.path.join(UPLOAD_FOLDER, user_id)
            os.makedirs(user_folder, exist_ok=True)

            for idx, image_file in enumerate(image_files):
                if image_file and allowed_file(image_file.filename):
                    filename = f"image{idx + 1}.{image_file.filename.rsplit('.', 1)[1].lower()}"
                    filepath = os.path.join(user_folder, filename)
                    image_file.save(filepath)
                    image_paths.append(f"/static/article_image/{user_id}/{filename}")
        
        article_data = {
            "title": title,
            "content": content,
            "user_id": user_id,
            "date": date,
            "category": category,
            "images": image_paths
        }
        
        result = articles_collection.insert_one(article_data)

        if result:
            return redirect(url_for("articles.index"))
            
    return render_template("write.html")