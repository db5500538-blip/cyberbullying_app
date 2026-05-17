from flask import Blueprint, render_template, redirect

pages = Blueprint("pages", __name__)

@pages.route("/")
def index():
    return redirect("/login.html")

@pages.route("/login.html")
def login_page():
    return render_template("login.html")

@pages.route("/register.html")
def register_page():
    return render_template("register.html")

@pages.route("/home.html")
def home_page():
    return render_template("home.html")

@pages.route("/profile.html")
def profile_page():
    return render_template("profile.html")

@pages.route("/explore.html")
def explore_page():
    return render_template("explore.html")