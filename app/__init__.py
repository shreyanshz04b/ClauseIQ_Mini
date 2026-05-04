import os
from flask import Flask, request
from dotenv import load_dotenv

# Load environment variables FIRST before importing Config
load_dotenv()

from .config import Config
from .extensions import db
from .routes.upload import upload_bp
from .routes.chat import chat_bp
from .routes.ingest import ingest_bp
from .routes.pages import pages_bp
from .routes.translation import translation_bp
from .routes.explorer import explorer_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)

    app.register_blueprint(pages_bp)
    app.register_blueprint(upload_bp, url_prefix="/api")
    app.register_blueprint(ingest_bp, url_prefix="/api")
    app.register_blueprint(chat_bp, url_prefix="/api")
    app.register_blueprint(translation_bp, url_prefix="/api")
    app.register_blueprint(explorer_bp)

    @app.after_request
    def add_no_cache_headers(response):
        if not request.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

    # Create all tables on startup
    with app.app_context():
        db.create_all()

    return app
