from . import db
from flask_login import UserMixin
from datetime import datetime

follows = db.Table('follows',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    profile_pic = db.Column(db.String(200), default='default.jpg')
    bio = db.Column(db.String(300), default='')
    is_admin = db.Column(db.Boolean, default=False)
    is_suspended = db.Column(db.Boolean, default=False)
    report_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    posts = db.relationship('Post', backref='author', lazy=True)
    sent_messages = db.relationship('Message',
        foreign_keys='Message.sender_id', backref='sender', lazy=True)
    received_messages = db.relationship('Message',
        foreign_keys='Message.receiver_id', backref='receiver', lazy=True)
    following = db.relationship('User',
        secondary=follows,
        primaryjoin=(follows.c.follower_id == id),
        secondaryjoin=(follows.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'),
        lazy='dynamic')

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    image = db.Column(db.String(200))
    caption = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    comments = db.relationship('Comment', backref='post', lazy=True)
    likes = db.relationship('Like', backref='post', lazy=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    content = db.Column(db.String(500))
    is_flagged = db.Column(db.Boolean, default=False)
    toxicity_score = db.Column(db.Float, default=0.0)
    is_blocked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='comments')

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.String(1000))
    is_flagged = db.Column(db.Boolean, default=False)
    toxicity_score = db.Column(db.Float, default=0.0)
    is_reported = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    reported_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content_type = db.Column(db.String(50))
    content_id = db.Column(db.Integer)
    severity = db.Column(db.String(20))
    is_reviewed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reporter = db.relationship('User', foreign_keys=[reporter_id])
    reported_user = db.relationship('User', foreign_keys=[reported_user_id])

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    message = db.Column(db.String(500))
    is_read = db.Column(db.Boolean, default=False)
    notif_type = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ProfileVisit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    visitor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    visited_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    visit_count = db.Column(db.Integer, default=1)
    last_visit = db.Column(db.DateTime, default=datetime.utcnow)
    notified = db.Column(db.Boolean, default=False)