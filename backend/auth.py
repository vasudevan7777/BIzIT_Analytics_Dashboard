"""
BizIT Analytics - Authentication Routes
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token, 
    jwt_required, get_jwt_identity, get_jwt
)
from datetime import datetime
from models import db, User
from functools import wraps

auth_bp = Blueprint('auth', __name__)

# Store for revoked tokens (in production, use Redis)
revoked_tokens = set()


def role_required(allowed_roles):
    """Decorator to check user roles"""
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            user_id = int(get_jwt_identity())
            user = User.query.get(user_id)
            if not user or user.role not in allowed_roles:
                return jsonify({'error': 'Access denied. Insufficient permissions.'}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'email', 'password']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Check if email already exists
    if User.query.filter_by(email=data['email'].lower()).first():
        return jsonify({'error': 'Email already registered'}), 409
    
    # Validate password strength
    password = data['password']
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    
    # Validate role
    allowed_roles = ['Admin', 'Business Manager', 'Analyst']
    role = data.get('role', 'Analyst')
    if role not in allowed_roles:
        return jsonify({'error': f'Invalid role. Allowed roles: {", ".join(allowed_roles)}'}), 400
    
    # Create new user
    user = User(
        name=data['name'],
        email=data['email'].lower(),
        role=role
    )
    user.set_password(password)
    
    try:
        db.session.add(user)
        db.session.commit()
        
        # Generate tokens (identity must be string for PyJWT 2.x)
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Registration failed. Please try again.'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return JWT tokens"""
    data = request.get_json()
    
    email = data.get('email', '').lower()
    password = data.get('password', '')
    remember_me = data.get('remember_me', False)
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'Account is deactivated. Contact admin.'}), 401
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Generate tokens (identity must be string for PyJWT 2.x)
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    
    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict(),
        'access_token': access_token,
        'refresh_token': refresh_token
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user and revoke token"""
    jti = get_jwt()['jti']
    revoked_tokens.add(jti)
    return jsonify({'message': 'Successfully logged out'}), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    user_id = get_jwt_identity()  # Already a string
    access_token = create_access_token(identity=user_id)
    return jsonify({'access_token': access_token}), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current authenticated user"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()}), 200


@auth_bp.route('/users', methods=['GET'])
@role_required(['Admin'])
def get_all_users():
    """Get all users (Admin only)"""
    users = User.query.all()
    return jsonify({'users': [user.to_dict() for user in users]}), 200


@auth_bp.route('/users/<int:user_id>', methods=['PUT'])
@role_required(['Admin'])
def update_user(user_id):
    """Update user details (Admin only)"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        user.name = data['name']
    if 'role' in data:
        user.role = data['role']
    if 'is_active' in data:
        user.is_active = data['is_active']
    if 'password' in data and data['password']:
        user.set_password(data['password'])
    
    db.session.commit()
    return jsonify({'message': 'User updated', 'user': user.to_dict()}), 200


@auth_bp.route('/users/<int:user_id>', methods=['DELETE'])
@role_required(['Admin'])
def delete_user(user_id):
    """Delete user (Admin only)"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted'}), 200


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({'error': 'Current and new password are required'}), 400
    
    if not user.check_password(current_password):
        return jsonify({'error': 'Current password is incorrect'}), 401
    
    if len(new_password) < 8:
        return jsonify({'error': 'New password must be at least 8 characters'}), 400
    
    user.set_password(new_password)
    db.session.commit()
    
    return jsonify({'message': 'Password changed successfully'}), 200


def is_token_revoked(jwt_header, jwt_payload):
    """Check if token is revoked"""
    jti = jwt_payload['jti']
    return jti in revoked_tokens
