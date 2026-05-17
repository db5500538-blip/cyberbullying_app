from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from .. import mango
from ..models import Message, User, Report
from ..ai.detector import analyze_text

messages = Blueprint('messages', __name__)

@messages.route('/messages/<int:user_id>')
@login_required
def chat(user_id):
    other = User.query.get_or_404(user_id)
    msgs = Message.query.filter(
        ((Message.sender_id == current_user.id) &
         (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) &
         (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at).all()
    return render_template('messages.html', other=other, messages=msgs)

@messages.route('/messages/<int:user_id>/send', methods=['POST'])
@login_required
def send_message(user_id):
    content = request.json.get('content')
    is_toxic, score, severity = analyze_text(content)
    msg = Message(
        sender_id=current_user.id,
        receiver_id=user_id,
        content=content,
        toxicity_score=score,
        is_flagged=is_toxic,
        is_reported=is_toxic
    )
    db.session.add(msg)
    if is_toxic:
        report = Report(
            reporter_id=user_id,
            reported_user_id=current_user.id,
            content_type='message',
            content_id=msg.id,
            severity=severity
        )
        db.session.add(report)
        user = User.query.get(current_user.id)
        user.report_count += 1
    db.session.commit()
    return jsonify({
        'content': content,
        'flagged': is_toxic,
        'severity': severity
    })