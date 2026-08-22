from flask import Flask, jsonify
import socket
import os

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({
        "message": "Hello from DevOps Platform demo-service!",
        "hostname": socket.gethostname(),
        "version": os.getenv("APP_VERSION", "dev")
    })

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
