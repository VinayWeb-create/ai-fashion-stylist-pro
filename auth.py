"""
Authentication module for AI Fashion Stylist
Handles JWT tokens, password hashing, and magic links
"""
import jwt
import bcrypt
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from config import Config
from models import User

# In-memory storage for magic link tokens (use Redis in production)
magic_link_tokens = {}

def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(Config.BCRYPT_ROUNDS)).decode('utf-8')

def verify_password(password, password_hash):
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def generate_jwt_token(user_id, email):
    """Generate JWT token for authenticated user"""
    payload = {
        'user_id': str(user_id),
        'email': email,
        'exp': datetime.utcnow() + timedelta(hours=Config.JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm=Config.JWT_ALGORITHM)

def verify_jwt_token(token):
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=[Config.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def generate_magic_link_token(email):
    """Generate a magic link token"""
    token = secrets.token_urlsafe(32)
    magic_link_tokens[token] = {
        'email': email,
        'expires_at': datetime.utcnow() + timedelta(minutes=Config.MAGIC_LINK_EXPIRATION_MINUTES)
    }
    return token

def verify_magic_link_token(token):
    """Verify magic link token"""
    if token not in magic_link_tokens:
        return None
    
    token_data = magic_link_tokens[token]
    if datetime.utcnow() > token_data['expires_at']:
        del magic_link_tokens[token]
        return None
    
    email = token_data['email']
    del magic_link_tokens[token]
    return email

def send_magic_link_email(email, token):
    """Send magic link email"""
    if not Config.SMTP_USER or not Config.SMTP_PASSWORD:
        # Email not configured, just return the link for development
        magic_link = f"{Config.FRONTEND_URL}/auth/verify?token={token}"
        print(f"Magic link for {email}: {magic_link}")
        return True
    
    try:
        magic_link = f"{Config.FRONTEND_URL}/auth/verify?token={token}"
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Your Fashion Stylist Login Link'
        msg['From'] = Config.FROM_EMAIL
        msg['To'] = email
        
        text = f"""
        Hi there!
        
        Click the link below to log in to your Fashion Stylist account:
        {magic_link}
        
        This link will expire in {Config.MAGIC_LINK_EXPIRATION_MINUTES} minutes.
        
        If you didn't request this, please ignore this email.
        
        Best regards,
        Fashion Stylist Team
        """
        
        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
              <h2 style="color: #2d1b4e;">Your Login Link</h2>
              <p>Hi there!</p>
              <p>Click the button below to log in to your Fashion Stylist account:</p>
              <div style="text-align: center; margin: 30px 0;">
                <a href="{magic_link}" 
                   style="background: linear-gradient(135deg, #d4af37 0%, #f0d98f 100%); 
                          color: white; 
                          padding: 14px 28px; 
                          text-decoration: none; 
                          border-radius: 8px; 
                          display: inline-block;
                          font-weight: 500;">
                  Log In to Fashion Stylist
                </a>
              </div>
              <p style="color: #666; font-size: 14px;">
                This link will expire in {Config.MAGIC_LINK_EXPIRATION_MINUTES} minutes.
              </p>
              <p style="color: #666; font-size: 14px;">
                If you didn't request this, please ignore this email.
              </p>
              <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
              <p style="color: #999; font-size: 12px;">
                Best regards,<br>
                Fashion Stylist Team
              </p>
            </div>
          </body>
        </html>
        """
        
        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))
        
        with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as server:
            server.starttls()
            server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def token_required(f):
    """Decorator to require JWT token for routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check for token in Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'status': 'error', 'message': 'Token is missing'}), 401
        
        payload = verify_jwt_token(token)
        if not payload:
            return jsonify({'status': 'error', 'message': 'Token is invalid or expired'}), 401
        
        # Add user info to request context
        request.current_user = payload
        
        return f(*args, **kwargs)
    
    return decorated

def optional_token(f):
    """Decorator for routes that work with or without authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check for token in Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if token:
            payload = verify_jwt_token(token)
            if payload:
                request.current_user = payload
            else:
                request.current_user = None
        else:
            request.current_user = None
        
        return f(*args, **kwargs)
    
    return decorated
