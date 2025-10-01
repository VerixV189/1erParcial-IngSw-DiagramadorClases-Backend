from app import create_app

app = create_app()

PORT = 8000
# host = '127.0.0.1'
host = '0.0.0.0'

if __name__ == "__main__":
    app.run(host = host, port=PORT,debug=True)
