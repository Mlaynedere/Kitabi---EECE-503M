import jwt
from datetime import datetime, timedelta
from flask import current_app, jsonify
from . import TokenExpiryTime
from .models import Customer

def create_access_token(user_id):
    """
    Generates an access token for a user.
    :param user_id: Unique identifier of the user
    :param expires_in: Expiration time in minutes
    :return: Encoded JWT token
    """
    user = Customer.query.get(user_id)
    if not user:
        raise ValueError("Invalid user ID")
    
    roles = [role.name for role in user.roles]

    payload = {
        'user_id': user_id,
        'roles': roles,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(minutes=TokenExpiryTime)
    }
    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
    return token

def decode_token(token):
    """
    Decodes a JWT token and verifies its validity.
    :param token: Encoded JWT token
    :return: Decoded payload or raises an error if invalid
    """
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401

