from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .. import mongo
from ..ai.detector import analyze_text
from bson import ObjectId
from datetime import datetime
import base64, os, uuid

posts = Blueprint("posts", __name__)
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "..", "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def post_to_dict(post, current_user_id=None):
    author = mongo.db.users.find_one({"_id": post["author_id"]})
    liked = current_user_id and ObjectId(current_user_id) in post.get("likes", [])
    return {
        "_id": str(post["_id"]),
        "caption": post.get("caption", ""),
        "image_url": post.get("image_url", ""),
        "author": {
            "_id": str(author["_id"]),
            "username": author["username"],
            "avatar": author.get("avatar", ""),
        } if author else {},
        "likes": len(post.get("likes", [])),
        "liked": bool(liked),
        "comments": [
            {"user_id": str(c["user_id"]), "username": c["username"],
             "text": c["text"], "created_at": c["created_at"].isoformat()}
            for c in post.get("comments", [])
        ],
        "created_at": post["created_at"].isoformat(),
    }

@posts.route("/", methods=["GET"])
@jwt_required()
def get_feed():
    uid = get_jwt_identity()
    user = mongo.db.users.find_one({"_id": ObjectId(uid)})
    ids = user.get("following", []) + [ObjectId(uid)]
    all_posts = list(mongo.db.posts.find(
        {"author_id": {"$in": ids}, "blocked": {"$ne": True}}
    ).sort("created_at", -1).limit(30))
    return jsonify([post_to_dict(p, uid) for p in all_posts]), 200

@posts.route("/explore", methods=["GET"])
@jwt_required()
def explore():
    uid = get_jwt_identity()
    all_posts = list(mongo.db.posts.find({"blocked": {"$ne": True}}).sort("created_at", -1).limit(50))
    return jsonify([post_to_dict(p, uid) for p in all_posts]), 200

@posts.route("/", methods=["POST"])
@jwt_required()
def create_post():
    uid = get_jwt_identity()
    data = request.get_json()
    caption = data.get("caption", "").strip()
    image_b64 = data.get("image_b64", "")

    analysis = {"action": "allow"}
    if caption:
        analysis = analyze_text(caption)
        if analysis["action"] == "block":
            return jsonify({"error": "Post blocked due to harmful content.", "analysis": analysis}), 403

    image_url = ""
    if image_b64:
        try:
            header, encoded = image_b64.split(",", 1) if "," in image_b64 else ("", image_b64)
            ext = "png" if "png" in header else "jpg"
            filename = f"{uuid.uuid4().hex}.{ext}"
            with open(os.path.join(UPLOAD_FOLDER, filename), "wb") as f:
                f.write(base64.b64decode(encoded))
            image_url = f"/static/uploads/{filename}"
        except Exception:
            pass

    post_id = mongo.db.posts.insert_one({
        "author_id": ObjectId(uid), "caption": caption, "image_url": image_url,
        "likes": [], "comments": [], "saved_by": [],
        "created_at": datetime.utcnow(), "blocked": False, "ai_analysis": analysis,
    }).inserted_id
    post = mongo.db.posts.find_one({"_id": post_id})
    result = post_to_dict(post, uid)
    result["warning"] = analysis["action"] == "warn"
    return jsonify(result), 201

@posts.route("/<post_id>/like", methods=["POST"])
@jwt_required()
def toggle_like(post_id):
    uid = get_jwt_identity()
    post = mongo.db.posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        return jsonify({"error": "Not found"}), 404
    uid_obj = ObjectId(uid)
    if uid_obj in post.get("likes", []):
        mongo.db.posts.update_one({"_id": ObjectId(post_id)}, {"$pull": {"likes": uid_obj}})
        liked = False
    else:
        mongo.db.posts.update_one({"_id": ObjectId(post_id)}, {"$addToSet": {"likes": uid_obj}})
        liked = True
        if str(post["author_id"]) != uid:
            me = mongo.db.users.find_one({"_id": uid_obj})
            mongo.db.notifications.insert_one({
                "recipient_id": post["author_id"], "sender_id": uid_obj,
                "sender_username": me["username"], "type": "like",
                "post_id": ObjectId(post_id),
                "message": f"{me['username']} liked your post",
                "read": False, "created_at": datetime.utcnow(),
            })
    post = mongo.db.posts.find_one({"_id": ObjectId(post_id)})
    return jsonify({"liked": liked, "likes": len(post.get("likes", []))}), 200

@posts.route("/<post_id>/comment", methods=["POST"])
@jwt_required()
def add_comment(post_id):
    uid = get_jwt_identity()
    data = request.get_json()
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "Comment cannot be empty"}), 400
    analysis = analyze_text(text)
    if analysis["action"] == "block":
        return jsonify({"error": "Comment blocked due to harmful content.", "analysis": analysis}), 403
    me = mongo.db.users.find_one({"_id": ObjectId(uid)})
    comment = {"user_id": ObjectId(uid), "username": me["username"],
               "text": text, "created_at": datetime.utcnow()}
    mongo.db.posts.update_one({"_id": ObjectId(post_id)}, {"$push": {"comments": comment}})
    post = mongo.db.posts.find_one({"_id": ObjectId(post_id)})
    if str(post["author_id"]) != uid:
        mongo.db.notifications.insert_one({
            "recipient_id": post["author_id"], "sender_id": ObjectId(uid),
            "sender_username": me["username"], "type": "comment",
            "post_id": ObjectId(post_id),
            "message": f"{me['username']} commented on your post",
            "read": False, "created_at": datetime.utcnow(),
        })
    return jsonify({"comment": {"username": me["username"], "text": text},
                    "warning": analysis["action"] == "warn"}), 201

@posts.route("/analyze", methods=["POST"])
@jwt_required()
def analyze_only():
    data = request.get_json()
    return jsonify(analyze_text(data.get("text", ""))), 200

@posts.route("/<post_id>", methods=["DELETE"])
@jwt_required()
def delete_post(post_id):
    uid = get_jwt_identity()
    post = mongo.db.posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        return jsonify({"error": "Not found"}), 404
    if str(post["author_id"]) != uid:
        return jsonify({"error": "Unauthorized"}), 403
    mongo.db.posts.delete_one({"_id": ObjectId(post_id)})
    return jsonify({"message": "Deleted"}), 200