from flask import Blueprint, render_template, redirect, url_for

pages_bp = Blueprint("pages", __name__)


@pages_bp.get("/")
def home_page():
    return redirect(url_for("pages.landing_page"))


@pages_bp.get("/chat")
def chat_page():
    return render_template("chat.html")


@pages_bp.get("/landing")
def landing_page():
    return render_template("landing.html")

@pages_bp.get("/translate")
def translate_page():
    return render_template("translate.html")

@pages_bp.get("/explorer")
def explorer_page():
    return "TEST: Explorer page is working!", 200
