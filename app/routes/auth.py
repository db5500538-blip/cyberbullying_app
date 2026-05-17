from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity,
    set_access_cookies, unset_jwt_cookies
)
from .. import mongo, bcrypt
from bson import ObjectId
from datetime import datetime, timedelta

auth = Blueprint("auth", __name__)

def user_to_dict(user):
    return {
        "_id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "bio": user.get("bio", ""),
        "avatar": user.get("avatar", ""),
        "followers": [str(f) for f in user.get("followers", [])],
        "following": [str(f) for f in user.get("following", [])],
    }

@auth.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    if not username or not email or not password:
        return jsonify({"error": "All fields required"}), 400
    if mongo.db.users.find_one({"$or": [{"username": username}, {"email": email}]}):
        return jsonify({"error": "Username or email already exists"}), 409
    hashed = bcrypt.generate_password_hash(password).decode("utf-8")
    user_id = mongo.db.users.insert_one({
        "username": username, "email": email, "password": hashed,
        "bio": "", "avatar": "", "followers": [], "following": [],
        "role": "user", "created_at": datetime.utcnow(),
    }).inserted_id
    token = create_access_token(identity=str(user_id), expires_delta=timedelta(days=7))
    user = mongo.db.users.find_one({"_id": user_id})
    resp = make_response(jsonify({"message": "Registered", "user": user_to_dict(user), "token": token}), 201)
    set_access_cookies(resp, token)
    return resp

@auth.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    identifier = data.get("username") or data.get("email", "")
    password = data.get("password", "")
    user = mongo.db.users.find_one(
        {"$or": [{"username": identifier}, {"email": identifier.lower()}]}
    )
    if not user or not bcrypt.check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid credentials"}), 401
    token = create_access_token(identity=str(user["_id"]), expires_delta=timedelta(days=7))
    resp = make_response(jsonify({"message": "Login successful", "user": user_to_dict(user), "token": token}), 200)
    set_access_cookies(resp, token)
    return resp

@auth.route("/logout", methods=["POST"])
def logout():
    resp = make_response(jsonify({"message": "Logged out"}), 200)
    unset_jwt_cookies(resp)
    return resp

@auth.route("/me", methods=["GET"])
@jwt_required()
def me():
    uid = get_jwt_identity()
    user = mongo.db.users.find_one({"_id": ObjectId(uid)})
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user_to_dict(user)), 200