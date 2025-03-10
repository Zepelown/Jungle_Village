from flask import Flask, render_template
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# MongoDB 연결 설정
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.get_database()

@app.route("/")
def home():
    return render_template("index.html", message="Hello, Flask with MongoDB!")

if __name__ == "__main__":
    app.run(debug=True)
