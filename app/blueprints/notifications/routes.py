"""Notifications routes."""
from flask import render_template, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from . import bp
from app.extensions import db
from app.models.notification import Notification


@bp.route('/')
@login_required
def index():
    bid = current_user.business_id
    ntype = request.args.get('type', '')
    query = Notification.query.filter_by(business_id=bid)
    if ntype:
        query = query.filter_by(type=ntype)
    notifications = query.order_by(Notification.created_at.desc()).limit(100).all()
    unread_count = Notification.query.filter_by(business_id=bid, is_read=False).count()
    return render_template('notifications/index.html', title='Notifications', notifications=notifications,
                            ntype=ntype, unread_count=unread_count)


@bp.route('/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_read(notif_id):
    n = Notification.query.filter_by(id=notif_id, business_id=current_user.business_id).first_or_404()
    n.is_read = True
    db.session.commit()
    return redirect(url_for('notifications.index'))


@bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    Notification.query.filter_by(business_id=current_user.business_id, is_read=False).update({'is_read': True})
    db.session.commit()
    return redirect(url_for('notifications.index'))


@bp.route('/api/unread-count')
@login_required
def unread_count_api():
    count = Notification.query.filter_by(business_id=current_user.business_id, is_read=False).count()
    return jsonify({'count': count})
