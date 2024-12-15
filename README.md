# Kitabi---EECE-503M


This repository contains a Flask-based web application with comprehensive security implementations, focused on the deployment of a secure backend. Below, you will find an overview of the implemented security measures, development setup, and setup instructions.

---

## Key Security Features

### 1. **Authentication & Session Management**
- **JWT Integration**:
  - `jwt_utils.py` handles JSON Web Tokens (JWTs) for stateless authentication.
  - Tokens include expiration (`TokenExpiryTime`) and roles/permissions.
  - JWTs are signed with secure keys managed in Flask's `__init__.py`.
- **Session Management**:
  - Flask-Login is utilized for session-based user management.
  - Authentication endpoints are protected with `login_required`.
 
### 2. **Role Based Access Control (RBAC)**
- **Role Enforcement**:
  - decorators.py includes a `role_required` decorator to restrict access to specific routes based on user roles.
  - Roles are extracted from JWTs or the authenticated user object.
  - Unauthorized access attempts are logged and result in appropriate error responses.

### 3. **CSRF Protection**
- Built-in CSRF token support through Flask-WTF forms (`LoginForm`, `SignUpForm`).
- Ensures all POST requests include a valid CSRF token to mitigate cross-site request forgery attacks.

### 4. **SQL Injection Prevention**
- **Parameterized Queries**:
  - `security.py` defines a `safe_query` function that uses parameterized queries, ensuring that raw SQL is never executed with user inputs.

### 5. **Secure Password Management**
- Passwords are hashed using `werkzeug.security.generate_password_hash` and verified with `check_password_hash`.
- Password policies enforced by `password_meets_requirements` include:
  - Minimum length.
  - Complexity requirements (uppercase, special characters, etc.).

### 6. **Secure File Uploads**
- Sanitization:
  - Uploaded filenames are cleaned with `werkzeug.utils.secure_filename`.
  - File types are validated using `magic` to prevent execution of malicious files.
- Storage:
  - Files are stored in a designated `media/` directory, avoiding direct execution.

### 7. **Input Sanitization**
- User inputs are sanitized using `bleach` and validated with `validators` to prevent XSS and injection attacks.

### 8. **Rate Limiting**
- Flask-Limiter is used to mitigate brute-force attacks by applying request rate limits on sensitive endpoints (e.g., login).

### 9. **Error Handling**
- Comprehensive error handling ensures sensitive information is not exposed in responses.
- Invalid tokens and database errors are logged while providing generic user-facing messages.

### 10. Secure Headers
- Content-Security-Policy to prevent XSS.
- Strict-Transport-Security to enforce HTTPS.
- X-Frame-Options to prevent clickjacking.
- X-Content-Type-Options to prevent MIME sniffing.

---

## Setup Instructions

### Prerequisites
- Python 3.8+

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/secure-flask-app.git
   cd Kitabi--EECE-503M

2. Create a virtual environment (recommended)
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

3. Install dependencies:
   ```bash
   pip install -r requirements.txt

### Usage
To start the application, simply run:
```bash
python main.py
```
Then navigate to http://localhost:5000 using any browser of your choice
