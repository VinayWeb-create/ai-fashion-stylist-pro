from flask import Blueprint, request, jsonify
import secrets
import os
from models import User
from auth import (
    hash_password, verify_password, generate_jwt_token, 
    generate_magic_link_token, verify_magic_link_token,
    send_magic_link_email, token_required
)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    profile = data.get('profile', {})
    
    if not email or not password:
        return jsonify({'status': 'error', 'message': 'Email and password are required'}), 400
    
    existing_user = User.find_by_email(email)
    if existing_user:
        return jsonify({'status': 'error', 'message': 'User already exists'}), 400
    
    password_hash = hash_password(password)
    user = User.create(email, password_hash, profile)
    
    token = generate_jwt_token(user['_id'], email)
    
    return jsonify({
        'status': 'success',
        'message': 'User registered successfully',
        'token': token,
        'user': {
            'id': str(user['_id']),
            'email': user['email'],
            'profile': user['profile']
        }
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login with email and password"""
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'status': 'error', 'message': 'Email and password are required'}), 400
    
    user = User.find_by_email(email)
    if not user:
        return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401
    
    if not verify_password(password, user['password_hash']):
        return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401
    
    token = generate_jwt_token(user['_id'], email)
    
    return jsonify({
        'status': 'success',
        'message': 'Login successful',
        'token': token,
        'user': {
            'id': str(user['_id']),
            'email': user['email'],
            'profile': user['profile']
        }
    })

@auth_bp.route('/magic-link', methods=['POST'])
def request_magic_link():
    """Request a magic link for passwordless login"""
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    
    if not email:
        return jsonify({'status': 'error', 'message': 'Email is required'}), 400
    
    user = User.find_by_email(email)
    if not user:
        password_hash = hash_password(secrets.token_urlsafe(32))
        user = User.create(email, password_hash)
    
    token = generate_magic_link_token(email)
    send_magic_link_email(email, token)
    
    return jsonify({
        'status': 'success',
        'message': 'Magic link sent to your email',
        'dev_token': token if not os.getenv('SMTP_USER') else None
    })

@auth_bp.route('/verify-magic', methods=['POST'])
def verify_magic():
    """Verify magic link token and log in"""
    data = request.get_json()
    token = data.get('token', '')
    
    if not token:
        return jsonify({'status': 'error', 'message': 'Token is required'}), 400
    
    email = verify_magic_link_token(token)
    if not email:
        return jsonify({'status': 'error', 'message': 'Invalid or expired token'}), 401
    
    user = User.find_by_email(email)
    if not user:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404
    
    jwt_token = generate_jwt_token(user['_id'], email)
    
    return jsonify({
        'status': 'success',
        'message': 'Login successful',
        'token': jwt_token,
        'user': {
            'id': str(user['_id']),
            'email': user['email'],
            'profile': user['profile']
        }
    })

@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user():
    """Get current user info"""
    user = User.find_by_id(request.current_user['user_id'])
    if not user:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404
    
    return jsonify({
        'status': 'success',
        'user': {
            'id': str(user['_id']),
            'email': user['email'],
            'profile': user['profile']
        }
    })

@auth_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile():
    """Update user profile"""
    data = request.get_json()
    profile = data.get('profile', {})
    
    user = User.update_profile(request.current_user['user_id'], profile)
    
    return jsonify({
        'status': 'success',
        'message': 'Profile updated successfully',
        'user': {
            'id': str(user['_id']),
            'email': user['email'],
            'profile': user['profile']
        }
    })
