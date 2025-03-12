from flask import Flask, render_template, request, redirect, url_for, flash
import os
from dotenv import load_dotenv
from flask_pymongo import PyMongo
from flask_mail import Mail, Message

# 애플리케이션 초기화

load_dotenv(override=True)

app = Flask(__name__)

MONGO_URI = os.getenv("MONGO_URI")
app.config['MONGO_URI'] = MONGO_URI
mongo = PyMongo(app)

SECRET_KEY = 'jungle_village_secret_key'

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'jungle.8.306.5@gmail.com' 
app.config['MAIL_PASSWORD'] = 'jhuv srgz mtdu pryi'  
app.config['MAIL_DEFAULT_SENDER'] = 'jungle.8.306.5@gmail.com'

mail = Mail(app)

from routes import articles
from routes import auth
# 블루프린트 등록
app.register_blueprint(articles.bp, url_prefix='/')
app.register_blueprint(auth.bp, url_prefix='/auth')

# 애플리케이션 반환
def create_app():
    return app