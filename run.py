from create_app import create_app

app = create_app()  # app.py에서 생성한 Flask 애플리케이션 인스턴스 가져오기

@app.route("/write")
def write():
    nickname="정글러"
    profile_img = None
    return render_template('write.html', nickname=nickname, profile_img=profile_img)

@app.route("/mypage")
def mypage():
    return render_template('mypage.html')

if __name__ == "__main__":
    app.run(debug=True)