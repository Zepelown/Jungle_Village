from flask import Flask, render_template
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# MongoDB 연결 설정
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.junglevillage


# 📌 Blueprint를 맨 아래에서 import해야 함!
from app.routes.articles import articles_bp  

app.register_blueprint(articles_bp, url_prefix="/articles")  # ✅ "/articles" 경로로 등록