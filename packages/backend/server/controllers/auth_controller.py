from flask import request, jsonify
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from models.db import db
from models.user import User
from models.user_preference import UserPreference
from datetime import datetime, timedelta
import uuid

def register():
    """Register a new user"""
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        # Validate input
        if not username or not email or not password:
            return jsonify({'message': 'All fields are required'}), 400
        
        # Check if user already exists
        existing_user = User.query.filter((User.email == email) | (User.username == username)).first()
        if existing_user:
            return jsonify({'message': 'User with this email or username already exists'}), 400
        
        # Create new user
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        
        # Create default user preferences
        new_preference = UserPreference(user_id=new_user.id)
        db.session.add(new_preference)
        db.session.commit()
        
        # Generate access token
        access_token = create_access_token(identity=new_user.id)
        
        return jsonify({
            'token': access_token,
            'user': new_user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Registration error: {str(e)}")
        return jsonify({'message': 'Server error during registration'}), 500

def login():
    """Login user and get token"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        # Validate input
        if not email or not password:
            return jsonify({'message': 'Email and password are required'}), 400
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return jsonify({'message': 'Invalid credentials'}), 401
        
        # Generate access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'token': access_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'message': 'Server error during login'}), 500

@jwt_required()
def get_current_user():
    """Get current user"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        print(f"Get current user error: {str(e)}")
        return jsonify({'message': 'Server error'}), 500

def request_password_reset():
    """Request a password reset token"""
    try:
        data = request.get_json()
        email = data.get('email')

        if not email:
            return jsonify({'message': 'Email is required'}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            # Return a generic message to prevent email enumeration
            return jsonify({'message': 'If an account with that email exists, a password reset link has been sent.'}), 200

        # Generate a unique token
        reset_token = str(uuid.uuid4())
        # Set token expiration (e.g., 1 hour from now)
        expiration = datetime.utcnow() + timedelta(hours=1)

        user.reset_token = reset_token
        user.reset_token_expiration = expiration
        db.session.commit()

        # In a real application, you would send an email here
        print(f"Password reset token for {user.email}: {reset_token}")

        return jsonify({'message': 'If an account with that email exists, a password reset link has been sent.'}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Request password reset error: {str(e)}")
        return jsonify({'message': 'Server error during password reset request'}), 500

def reset_password():
    """Reset user password using a token"""
    try:
        data = request.get_json()
        token = data.get('token')
        new_password = data.get('new_password')

        if not token or not new_password:
            return jsonify({'message': 'Token and new password are required'}), 400

        user = User.query.filter_by(reset_token=token).first()

        if not user or user.reset_token_expiration < datetime.utcnow():
            return jsonify({'message': 'Invalid or expired token'}), 400

        user.set_password(new_password)
        user.reset_token = None  # Invalidate token
        user.reset_token_expiration = None
        db.session.commit()

        return jsonify({'message': 'Password has been reset successfully.'}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Reset password error: {str(e)}")
        return jsonify({'message': 'Server error during password reset'}), 500
