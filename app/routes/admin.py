from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from .. import db
from ..models import User, Report, Notification

admin = Blueprint('admin', __name__)

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@admin.route('/dashboard')
@login_required
@admin_required
def dashboard():
    reports = Report.query.filter_by(is_reviewed=False).all()
    users = User.query.filter_by(is_admin=False).all()
    return render_template('admin/dashboard.html',
        reports=reports, users=users)

@admin.route('/action/<int:user_id>/<action>')
@login_required
@admin_required
def take_action(user_id, action):
    user = User.query.get(user_id)
    if action == 'warn':
        notif = Notification(
            user_id=user_id,
            message='⚠️ Warning: You violated our community guidelines.',
            notif_type='warning'
        )
        db.session.add(notif)
    elif action == 'suspend':
        user.is_suspended = True
    elif action == 'delete':
        db.session.delete(user)
    db.session.commit()
    return redirect(url_for('admin.dashboard'))

@admin.route('/review/<int:report_id>')
@login_required
@admin_required
def review_report(report_id):
    report = Report.query.get(report_id)
    report.is_reviewed = True
    db.session.commit()
    return redirect(url_for('admin.dashboard'))