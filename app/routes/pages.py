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

@pages.route("/messages.html")
def messages_page():
    return render_template("messages.html")

@pages.route("/notifications.html")
def notifications_page():
    return render_template("notifications.html")

@pages.route("/edit-profile.html")
def edit_profile_page():
    return render_template("edit_profile.html")

@pages.route("/admin.html")
def admin_page():
    return render_template("admin.html")