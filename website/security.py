# website/security.py
import bleach
from flask import request
import magic
import validators
import uuid
import os
import re
from werkzeug.utils import secure_filename
from werkzeug.exceptions import SecurityError
from datetime import datetime
from . import db

def safe_query(query, params):
    """Prevent SQL injection by using parameterized queries"""
    from .admin import log_activity

    try:
        result = db.session.execute(query, params)
        return result
    except Exception as e:
        log_activity('database_error', details=str(e))
        raise

def sanitize_input(text):
    """Sanitize user input to prevent XSS attacks"""
    return bleach.clean(text, strip=True)

def validate_url(url_string):
    """Validate URLs to prevent SSRF attacks"""
    return bool(validators.url(url_string))

def secure_file_upload(file, upload_folder='./media'):
    """Enhanced security for file uploads"""
    if file and allowed_file(file.filename):
        original_filename = secure_filename(file.filename)
        
        # Read file content for type checking
        file_content = file.read()
        file.seek(0)  # Reset file pointer
        
        # Check file type using magic numbers
        file_type = magic.from_buffer(file_content, mime=True)
        if file_type not in ['image/jpeg', 'image/png', 'image/gif']:
            raise SecurityError("Invalid file type")
        
        # Generate random filename
        safe_filename = f"{uuid.uuid4()}{os.path.splitext(original_filename)[1]}"
        file_path = os.path.join(upload_folder, safe_filename)
        
        return file_path
    return None

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def password_meets_requirements(password):
    """Check password strength"""
    if len(password) < 12:
        return False, "Password must be at least 12 characters long"
    if not re.search("[a-z]", password):
        return False, "Password must contain lowercase letters"
    if not re.search("[A-Z]", password):
        return False, "Password must contain uppercase letters"
    if not re.search("[0-9]", password):
        return False, "Password must contain numbers"
    if not re.search("[!@#$%^&*()]", password):
        return False, "Password must contain special characters"
    return True, "Password meets requirements"

# Account lockout functionality
class LoginAttemptTracker:
    def __init__(self):
        self.attempts = {}
        self.lockout_duration = 900  # 15 minutes in seconds

    def add_attempt(self, user_id):
        current_time = datetime.utcnow()
        if user_id not in self.attempts:
            self.attempts[user_id] = {'count': 1, 'timestamp': current_time}
        else:
            self.attempts[user_id]['count'] += 1
            self.attempts[user_id]['timestamp'] = current_time

    def is_locked_out(self, user_id):
        if user_id not in self.attempts:
            return False
        
        current_time = datetime.utcnow()
        attempt_info = self.attempts[user_id]
        
        # Check if lockout duration has passed
        if (current_time - attempt_info['timestamp']).total_seconds() > self.lockout_duration:
            del self.attempts[user_id]
            return False
            
        return attempt_info['count'] >= 5  # Lock after 5 attempts

    def reset_attempts(self, user_id):
        if user_id in self.attempts:
            del self.attempts[user_id]

# Initialize login attempt tracker
login_tracker = LoginAttemptTracker()

# Two-factor authentication functions
def generate_2fa_code():
    """Generate a 6-digit 2FA code"""
    import random
    return str(random.randint(100000, 999999))

def send_2fa_code(email, code):
    """Send 2FA code via email"""
    # Implement email sending functionality
    pass

# Session security
def create_secure_session(user):
    """Create a secure session with proper flags"""
    from flask import session
    session.permanent = True
    session['user_id'] = user.id
    session['created_at'] = datetime.utcnow().timestamp()
    session['ip_address'] = request.remote_addr
    session['user_agent'] = request.user_agent.string

def validate_session():
    """Validate current session security"""
    from flask import session
    if 'created_at' not in session:
        return False
    
    # Check session age
    age = datetime.utcnow().timestamp() - session['created_at']
    if age > 1800:  # 30 minutes
        return False
    
    # Check if IP changed
    if session.get('ip_address') != request.remote_addr:
        return False
    
    # Check if user agent changed
    if session.get('user_agent') != request.user_agent.string:
        return False
    
    return True