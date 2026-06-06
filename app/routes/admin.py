from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .. import mongo
from bson import ObjectId

admin = Blueprint("admin", __name__)

def is_admin(uid):
    user = mongo.db.users.find_one({"_id": ObjectId(uid)})
    return user and user.get("role") == "admin"

@admin.route("/stats", methods=["GET"])
@jwt_required()
def stats():
    uid = get_jwt_identity()
    if not is_admin(uid):
        return jsonify({"error": "Unauthorized"}), 403
    return jsonify({
        "users": mongo.db.users.count_documents({}),
        "posts": mongo.db.posts.count_documents({}),
        "blocked_posts": mongo.db.posts.count_documents({"blocked": True}),
        "messages": mongo.db.messages.count_documents({})
    }), 200

@admin.route("/users", methods=["GET"])
@jwt_required()
def get_users():
    uid = get_jwt_identity()
    if not is_admin(uid):
        return jsonify({"error": "Unauthorized"}), 403
    users = list(mongo.db.users.find())
    return jsonify([{
        "_id": str(u["_id"]),
        "username": u["username"],
        "email": u["email"],
        "role": u.get("role", "user"),
        "banned": u.get("banned", False)
    } for u in users]), 200

@admin.route("/users/<uid>/ban", methods=["POST"])
@jwt_required()
def ban_user(uid):
    me = get_jwt_identity()
    if not is_admin(me):
        return jsonify({"error": "Unauthorized"}), 403
    ban = request.get_json().get("ban", True)
    mongo.db.users.update_one({"_id": ObjectId(uid)}, {"$set": {"banned": ban}})
    return jsonify({"message": "Done"}), 200

@admin.route("/users/<uid>", methods=["DELETE"])
@jwt_required()
def delete_user(uid):
    me = get_jwt_identity()
    if not is_admin(me):
        return jsonify({"error": "Unauthorized"}), 403
    mongo.db.users.delete_one({"_id": ObjectId(uid)})
    mongo.db.posts.delete_many({"author_id": ObjectId(uid)})
    return jsonify({"message": "Deleted"}), 200

@admin.route("/users/<uid>/make-admin", methods=["POST"])
@jwt_required()
def make_admin(uid):
    me = get_jwt_identity()
    if not is_admin(me):
        return jsonify({"error": "Unauthorized"}), 403
    mongo.db.users.update_one({"_id": ObjectId(uid)}, {"$set": {"role": "admin"}})
    return jsonify({"message": "Done"}), 200

@admin.route("/posts", methods=["GET"])
@jwt_required()
def get_posts():
    me = get_jwt_identity()
    if not is_admin(me):
        return jsonify({"error": "Unauthorized"}), 403
    posts = list(mongo.db.posts.find().sort("created_at", -1).limit(100))
    result = []
    for p in posts:
        author = mongo.db.users.find_one({"_id": p["author_id"]})
        result.append({
            "_id": str(p["_id"]),
            "author": author["username"] if author else "unknown",
            "caption": p.get("caption", ""),
            "blocked": p.get("blocked", False)
        })
    return jsonify(result), 200

@admin.route("/posts/<post_id>/block", methods=["POST"])
@jwt_required()
def block_post(post_id):
    me = get_jwt_identity()
    if not is_admin(me):
        return jsonify({"error": "Unauthorized"}), 403
    block = request.get_json().get("block", True)
    mongo.db.posts.update_one({"_id": ObjectId(post_id)}, {"$set": {"blocked": block}})
    return jsonify({"message": "Done"}), 200

@admin.route("/posts/<post_id>", methods=["DELETE"])
@jwt_required()
def delete_post(post_id):
    me = get_jwt_identity()
    if not is_admin(me):
        return jsonify({"error": "Unauthorized"}), 403
    mongo.db.posts.delete_one({"_id": ObjectId(post_id)})
    return jsonify({"message": "Deleted"}), 200