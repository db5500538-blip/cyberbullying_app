from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .. import mongo
from bson import ObjectId
from datetime import datetime
import base64, os, uuid

users = Blueprint("users", __name__)
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "..", "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def user_to_dict(user, current_user_id=None):
    is_following = current_user_id and ObjectId(current_user_id) in user.get("followers", [])
    return {
        "_id": str(user["_id"]),
        "username": user["username"],
        "bio": user.get("bio", ""),
        "avatar": user.get("avatar", ""),
        "followers_count": len(user.get("followers", [])),
        "following_count": len(user.get("following", [])),
        "is_following": bool(is_following),
    }

@users.route("/search", methods=["GET"])
@jwt_required()
def search_users():
    q = request.args.get("q", "").strip()
    uid = get_jwt_identity()
    if not q:
        return jsonify([]), 200
    results = list(mongo.db.users.find(
        {"username": {"$regex": q, "$options": "i"}, "_id": {"$ne": ObjectId(uid)}}
    ).limit(10))
    return jsonify([user_to_dict(u, uid) for u in results]), 200

@users.route("/suggestions", methods=["GET"])
@jwt_required()
def suggestions():
    uid = get_jwt_identity()
    user = mongo.db.users.find_one({"_id": ObjectId(uid)})
    excluded = user.get("following", []) + [ObjectId(uid)]
    suggested = list(mongo.db.users.find({"_id": {"$nin": excluded}}).limit(5))
    return jsonify([user_to_dict(u, uid) for u in suggested]), 200

@users.route("/<username>", methods=["GET"])
@jwt_required()
def get_profile(username):
    uid = get_jwt_identity()
    user = mongo.db.users.find_one({"username": username})
    if not user:
        return jsonify({"error": "User not found"}), 404
    posts = list(mongo.db.posts.find(
        {"author_id": user["_id"], "blocked": {"$ne": True}}
    ).sort("created_at", -1))
    return jsonify({
        "user": user_to_dict(user, uid),
        "posts": [{"_id": str(p["_id"]), "image_url": p.get("image_url",""),
                   "caption": p.get("caption",""), "likes": len(p.get("likes",[])),
                   "comments": len(p.get("comments",[]))} for p in posts]
    }), 200

@users.route("/<user_id>/follow", methods=["POST"])
@jwt_required()
def follow_user(user_id):
    uid = get_jwt_identity()
    if uid == user_id:
        return jsonify({"error": "Cannot follow yourself"}), 400
    target = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not target:
        return jsonify({"error": "Not found"}), 404
    me_obj, target_obj = ObjectId(uid), ObjectId(user_id)
    if me_obj in target.get("followers", []):
        mongo.db.users.update_one({"_id": target_obj}, {"$pull": {"followers": me_obj}})
        mongo.db.users.update_one({"_id": me_obj}, {"$pull": {"following": target_obj}})
        return jsonify({"following": False}), 200
    else:
        mongo.db.users.update_one({"_id": target_obj}, {"$addToSet": {"followers": me_obj}})
        mongo.db.users.update_one({"_id": me_obj}, {"$addToSet": {"following": target_obj}})
        me = mongo.db.users.find_one({"_id": me_obj})
        mongo.db.notifications.insert_one({
            "recipient_id": target_obj, "sender_id": me_obj,
            "sender_username": me["username"], "type": "follow",
            "message": f"{me['username']} started following you",
            "read": False, "created_at": datetime.utcnow(),
        })
        return jsonify({"following": True}), 200

@users.route("/me/update", methods=["PUT"])
@jwt_required()
def update_profile():
    uid = get_jwt_identity()
    data = request.get_json()
    updates = {}
    if "bio" in data:
        updates["bio"] = data["bio"][:150]
    if "avatar_b64" in data:
        try:
            header, encoded = data["avatar_b64"].split(",", 1) if "," in data["avatar_b64"] else ("", data["avatar_b64"])
            ext = "png" if "png" in header else "jpg"
            filename = f"avatar_{uuid.uuid4().hex}.{ext}"
            with open(os.path.join(UPLOAD_FOLDER, filename), "wb") as f:
                f.write(base64.b64decode(encoded))
            updates["avatar"] = f"/static/uploads/{filename}"
        except Exception:
            pass
    if updates:
        mongo.db.users.update_one({"_id": ObjectId(uid)}, {"$set": updates})
    user = mongo.db.users.find_one({"_id": ObjectId(uid)})
    return jsonify(user_to_dict(user)), 200