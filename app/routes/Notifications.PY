from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .. import mongo
from bson import ObjectId
from datetime import datetime

notifications = Blueprint("notifications", __name__)


def notif_to_dict(n):
    created = n.get("created_at", datetime.utcnow())
    now = datetime.utcnow()
    diff = now - created
    if diff.seconds < 60:
        time_str = "just now"
    elif diff.seconds < 3600:
        time_str = f"{diff.seconds // 60}m ago"
    elif diff.days == 0:
        time_str = f"{diff.seconds // 3600}h ago"
    else:
        time_str = f"{diff.days}d ago"

    return {
        "_id": str(n["_id"]),
        "type": n.get("type", ""),
        "message": n.get("message", ""),
        "sender_username": n.get("sender_username", ""),
        "sender_avatar": n.get("sender_avatar", ""),
        "post_id": str(n["post_id"]) if n.get("post_id") else None,
        "read": n.get("read", False),
        "time": time_str,
    }


@notifications.route("/", methods=["GET"])
@jwt_required()
def get_notifications():
    uid = get_jwt_identity()
    notifs = list(mongo.db.notifications.find(
        {"recipient_id": ObjectId(uid)}
    ).sort("created_at", -1).limit(30))
    return jsonify([notif_to_dict(n) for n in notifs]), 200


@notifications.route("/unread-count", methods=["GET"])
@jwt_required()
def unread_count():
    uid = get_jwt_identity()
    count = mongo.db.notifications.count_documents(
        {"recipient_id": ObjectId(uid), "read": False}
    )
    return jsonify({"count": count}), 200


@notifications.route("/mark-read", methods=["POST"])
@jwt_required()
def mark_all_read():
    uid = get_jwt_identity()
    mongo.db.notifications.update_many(
        {"recipient_id": ObjectId(uid), "read": False},
        {"$set": {"read": True}}
    )
    return jsonify({"message": "Marked all read"}), 200