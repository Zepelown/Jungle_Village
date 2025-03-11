from flask import Blueprint, render_template, request, redirect, url_for, flash
from bson.objectid import ObjectId
from app import db

# ✅ Blueprint 선언 (중복 제거)
articles_bp = Blueprint("articles", __name__)

articles_collection = db.articles  # 게시글 컬렉션

# ✅ 게시글 목록
@articles_bp.route("/")
def articles_list():
    articles = list(articles_collection.find())
    return render_template("articles.html", articles=articles)

# ✅ 게시글 상세 보기
@articles_bp.route("/<article_id>")
def article_detail(article_id):
    article = articles_collection.find_one({"_id": ObjectId(article_id)})
    if not article:
        flash("게시글을 찾을 수 없습니다.", "danger")
        return redirect(url_for("articles.articles_list"))

    return render_template("article_detail.html", article=article)
