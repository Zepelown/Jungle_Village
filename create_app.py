from flask import Flask, render_template, request, redirect, url_for, flash
import os
from dotenv import load_dotenv
from flask_pymongo import PyMongo

# 애플리케이션 초기화

load_dotenv()

app = Flask(__name__)

MONGO_URI = os.getenv("MONGO_URI")
app.config['MONGO_URI'] = MONGO_URI
mongo = PyMongo(app)

from routes import articles
# 블루프린트 등록
app.register_blueprint(articles.bp, url_prefix='/')

# 애플리케이션 반환
def create_app():
    return app