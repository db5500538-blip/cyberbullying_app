from flask import Flask
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import Config

mongo = PyMongo()
bcrypt = Bcrypt()
jwt = JWTManager()

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

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
        from .routes.pages import pages   # ← new file you'll add in Step 9

        app.register_blueprint(auth, url_prefix="/api/auth")
        app.register_blueprint(posts, url_prefix="/api/posts")
        app.register_blueprint(users, url_prefix="/api/users")
        # app.register_blueprint(messages, url_prefix="/api/messages")
        # app.register_blueprint(admin, url_prefix="/api/admin")
        app.register_blueprint(pages)

    return app