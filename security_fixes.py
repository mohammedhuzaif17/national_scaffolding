# Security Fixes for Your Application
# This code addresses the security issues found in your logs

from flask import Flask, request, jsonify, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime, timedelta
import logging
from functools import wraps
import hashlib

# Configure logging
logging.basicConfig(
    filename='security.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-this'  # CHANGE THIS!

# Rate Limiter Setup
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Failed login tracking
failed_attempts = {}
LOCKOUT_DURATION = 15  # minutes
MAX_ATTEMPTS = 5

def is_ip_blocked(ip):
    """Check if IP is temporarily blocked due to failed attempts"""
    if ip in failed_attempts:
        attempts, last_attempt = failed_attempts[ip]
        if attempts >= MAX_ATTEMPTS:
            if datetime.now() - last_attempt < timedelta(minutes=LOCKOUT_DURATION):
                return True
            else:
                # Reset after lockout period
                del failed_attempts[ip]
    return False

def record_failed_attempt(ip):
    """Record a failed login attempt"""
    if ip in failed_attempts:
        attempts, _ = failed_attempts[ip]
        failed_attempts[ip] = (attempts + 1, datetime.now())
    else:
        failed_attempts[ip] = (1, datetime.now())

def clear_failed_attempts(ip):
    """Clear failed attempts after successful login"""
    if ip in failed_attempts:
        del failed_attempts[ip]

def get_real_ip():
    """Get real IP address even behind proxy"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr

# Custom 404 handler to prevent information disclosure
@app.errorhandler(404)
def not_found(e):
    logging.warning(f"404 attempt from {get_real_ip()}: {request.path}")
    return jsonify({"error": "Not Found"}), 404

# Custom 405 handler
@app.errorhandler(405)
def method_not_allowed(e):
    logging.warning(f"405 attempt from {get_real_ip()}: {request.method} {request.path}")
    return jsonify({"error": "Method Not Allowed"}), 405

# Admin login with security
@app.route('/admin_login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")  # Strict rate limit on login
def admin_login():
    if request.method == 'POST':
        ip = get_real_ip()
        
        # Check if IP is blocked
        if is_ip_blocked(ip):
            logging.warning(f"Blocked IP attempted login: {ip}")
            return jsonify({
                "error": "Too many failed attempts. Please try again later."
            }), 429
        
        username = request.form.get('username')
        password = request.form.get('password')
        panel = request.form.get('panel', 'unknown')
        
        # Log the attempt
        logging.info(f"Login attempt from {ip}: username={username}, panel={panel}")
        
        # Validate credentials (replace with your actual validation)
        if validate_admin_credentials(username, password):
            clear_failed_attempts(ip)
            session['admin_logged_in'] = True
            session['username'] = username
            logging.info(f"Successful login: {username} from {ip}")
            return jsonify({"success": True, "redirect": "/admin_dashboard"})
        else:
            record_failed_attempt(ip)
            attempts_left = MAX_ATTEMPTS - failed_attempts[ip][0]
            logging.warning(f"Failed login attempt: {username} from {ip} ({attempts_left} attempts remaining)")
            return jsonify({
                "error": "Invalid credentials",
                "attempts_remaining": max(0, attempts_left)
            }), 401
    
    # GET request - show login form
    return render_login_form()

def validate_admin_credentials(username, password):
    """
    Validate admin credentials
    REPLACE THIS with your actual credential validation
    Use hashed passwords, NOT plain text!
    """
    # Example - DO NOT USE IN PRODUCTION
    # Use proper password hashing like bcrypt or argon2
    ADMIN_USERS = {
        'admin': hashlib.sha256('YourSecurePassword123!'.encode()).hexdigest()
    }
    
    if username in ADMIN_USERS:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return password_hash == ADMIN_USERS[username]
    return False

def render_login_form():
    """Render login form (replace with your actual template)"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Login</title>
        <link rel="stylesheet" href="/static/css/style.css">
    </head>
    <body>
        <div class="login-container">
            <img src="/static/images/logo.jpeg" alt="Logo">
            <h2>Admin Login</h2>
            <form id="loginForm">
                <input type="text" name="username" placeholder="Username" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Login</button>
                <div id="message"></div>
            </form>
        </div>
        <script>
            document.getElementById('loginForm').onsubmit = async (e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                const response = await fetch('/admin_login', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                if (data.success) {
                    window.location.href = data.redirect;
                } else {
                    document.getElementById('message').textContent = 
                        data.error + (data.attempts_remaining !== undefined 
                            ? ` (${data.attempts_remaining} attempts remaining)` 
                            : '');
                }
            };
        </script>
    </body>
    </html>
    '''

# Require authentication decorator
def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

# Protected admin routes
@app.route('/admin_dashboard')
@require_admin
def admin_dashboard():
    return "Welcome to Admin Dashboard"

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)