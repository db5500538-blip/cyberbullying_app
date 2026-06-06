from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .. import mongo
from bson import ObjectId
from datetime import datetime

messages = Blueprint("messages", __name__)

def fmt_time(dt):
    now = datetime.utcnow()
    diff = int((now - dt).total_seconds())
    if diff < 60: return "just now"
    if diff < 3600: return f"{diff//60}m ago"
    if diff < 86400: return f"{diff//3600}h ago"
    return dt.strftime("%b %d")

@messages.route("/conversations", methods=["GET"])
@jwt_required()
def get_conversations():
    uid = get_jwt_identity()
    pipeline = [
        {"$match": {"$or": [{"sender_id": ObjectId(uid)}, {"recipient_id": ObjectId(uid)}]}},
        {"$sort": {"created_at": -1}},
        {"$group": {
            "_id": {"$cond": [{"$eq": ["$sender_id", ObjectId(uid)]}, "$recipient_id", "$sender_id"]},
            "last_message": {"$first": "$text"},
            "last_time": {"$first": "$created_at"},
            "unread": {"$sum": {"$cond": [{"$and": [{"$eq": ["$recipient_id", ObjectId(uid)]}, {"$eq": ["$read", False]}]}, 1, 0]}}
        }}
    ]
    convs = list(mongo.db.messages.aggregate(pipeline))
    result = []
    for c in convs:
        user = mongo.db.users.find_one({"_id": c["_id"]})
        if user:
            result.append({
                "user_id": str(c["_id"]),
                "username": user["username"],
                "last_message": c["last_message"],
                "last_time": fmt_time(c["last_time"]),
                "unread": c["unread"] > 0
            })
    return jsonify(result), 200

@messages.route("/<recipient_id>", methods=["GET"])
@jwt_required()
def get_messages(recipient_id):
    uid = get_jwt_identity()
    msgs = list(mongo.db.messages.find({
        "$or": [
            {"sender_id": ObjectId(uid), "recipient_id": ObjectId(recipient_id)},
            {"sender_id": ObjectId(recipient_id), "recipient_id": ObjectId(uid)}
        ]
    }).sort("created_at", 1))
    mongo.db.messages.update_many(
        {"sender_id": ObjectId(recipient_id), "recipient_id": ObjectId(uid), "read": False},
        {"$set": {"read": True}}
    )
    return jsonify([{
        "sender_id": str(m["sender_id"]),
        "text": m["text"],
        "time": fmt_time(m["created_at"]),
        "read": m.get("read", False)
    } for m in msgs]), 200

@messages.route("/<recipient_id>", methods=["POST"])
@jwt_required()
def send_message(recipient_id):
    uid = get_jwt_identity()
    data = request.get_json()
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "Empty message"}), 400
    mongo.db.messages.insert_one({
        "sender_id": ObjectId(uid),
        "recipient_id": ObjectId(recipient_id),
        "text": text,
        "read": False,
        "created_at": datetime.utcnow()
    })
    return jsonify({"message": "Sent"}), 201