import os
from flask import Flask, jsonify

class Config:
    @property
    def CORS_ORIGINS(self):
        return os.getenv("CORS_ORIGINS", "http://localhost:5173")
    @property
    def SECRET_KEY(self):
        return os.getenv("SECRET_KEY", "dev-secret")

cfg = Config()

app = Flask(__name__)
app.config.from_object(cfg)
app.config["ENV"] = os.getenv("FLASK_ENV", "development")

@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=os.getenv("FLASK_DEBUG", "False").lower() == "true")