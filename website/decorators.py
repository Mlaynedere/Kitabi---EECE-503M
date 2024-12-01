from functools import wraps
from flask import redirect, url_for, flash, jsonify
from .models import ActivityLog, Customer
from . import db
from flask import request
from flask_login import current_user
from .jwt_utils import decode_token



def admin_required(f):
    """Admin authorization decorator - validates admin roles after JWT authentication"""
    @wraps(f)
    @jwt_required  # First verify the JWT token
    def decorated_function(*args, **kwargs):
        admin_roles = ['Super Admin', 'Product Manager', 'Order Manager']
        if not any(role in request.user_roles for role in admin_roles):
            return jsonify({'error': 'Admin privileges required'}), 403
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

def require_role(*roles):
    """Decorator to check for specific roles"""
    def decorator(f):
        @wraps(f)
        @jwt_required
        def decorated_function(*args, **kwargs):
            user_roles = request.user_roles
            if not any(role in roles for role in user_roles):
                return jsonify({'error': f'Required role(s): {", ".join(roles)}'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def jwt_required(f):
    """
    Decorator to protect routes with JWT authentication.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        cookie_token = request.cookies.get('jwt_token')
        token = cookie_token
        if not token:
            print("No token found in headers or cookies")  # Debug log
            return jsonify({'error': 'Authorization token is missing'}), 403
        try:
            payload = decode_token(token)
            if not payload:
                print("Token decode failed")  # Debug log
                return jsonify({'error': 'Invalid token'}), 401
            # Get user and store in request context
            user = Customer.query.get(payload['user_id'])
            if not user:
                print(f"User not found for id: {payload.get('user_id')}")  # Debug log
                return jsonify({'error': 'User not found'}), 401
                
            # Store in request context
            request.user = user
            request.user_roles = payload.get('roles', [])
            return f(*args, **kwargs)
            
        except Exception as e:
            print(f"JWT Verification failed: {str(e)}")
            return jsonify({'error': 'Invalid token'}), 401
            
    return decorated_function