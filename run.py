from create_app import create_app

app = create_app()  # app.py에서 생성한 Flask 애플리케이션 인스턴스 가져오기

if __name__ == "__main__":
    app.run(debug=True)