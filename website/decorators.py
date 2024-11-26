from functools import wraps
from flask import redirect, url_for, flash
from .models import ActivityLog
from . import db
from flask import request
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('views.home'))
        return f(*args, **kwargs)
    return decorated_function

def log_activity(action, entity_type=None, entity_id=None, details=None):
    try:
        log = ActivityLog(
            user_id=current_user.id if current_user.is_authenticated else None,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"Error logging activity: {e}")
        db.session.rollback()



def check_permission(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.has_permission(permission):
                log_activity(
                    action='permission_denied',
                    entity_type='permission',
                    details={
                        'route': request.path,
                        'permission': permission,
                        'user': current_user.username if current_user.is_authenticated else 'Guest',
                        'ip_address': request.remote_addr
                    }
                )
                flash('Access denied. Required permission not found.', 'error')
                return redirect(url_for('views.home'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator