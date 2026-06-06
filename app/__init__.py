from flask import Flask
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv
import os


load_dotenv()

mongo = PyMongo()
bcrypt = Bcrypt()
jwt = JWTManager()

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
    app.config["MONGO_URI"] = os.getenv("MONGO_URI", "")
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "jwt-secret")
    app.config["JWT_TOKEN_LOCATION"] = ["headers", "cookies"]
    app.config["JWT_COOKIE_CSRF_PROTECT"] = False
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

    CORS(app, supports_credentials=True)
    mongo.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    with app.app_context():
        from .routes.auth import auth
        from .routes.posts import posts
        from .routes.users import users
        # from .routes.messages import messages
        # from .routes.admin import admin
        from .routes.pages import pages

        app.register_blueprint(auth, url_prefix="/api/auth")
        app.register_blueprint(posts, url_prefix="/api/posts")
        app.register_blueprint(users, url_prefix="/api/users")
        app.register_blueprint(messages, url_prefix="/api/messages")
        app.register_blueprint(admin, url_prefix="/api/admin")
        app.register_blueprint(pages)

    return app