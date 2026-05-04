import os

class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret")

    _basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    _instance_dir = os.path.join(_basedir, "instance")

    SQLALCHEMY_DATABASE_URI = f"sqlite:///{_instance_dir}/local.db".replace("\\", "/")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    OLLAMA_BASE_URL = "http://localhost:11434"
    OLLAMA_CHAT_MODEL = "phi3:mini"
    OLLAMA_EMBED_MODEL = "nomic-embed-text:latest"

    MAX_UPLOAD_MB = 25
    UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")

    APP_BASE_URL = "http://127.0.0.1:5000"