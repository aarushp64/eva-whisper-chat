from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.db import db
from models.user import User
from models.user_preference import UserPreference, MemorizedDetail, Topic
from ml.user_personalization import UserPersonalizationModel
from datetime import datetime
import json

@jwt_required()
def analyze_conversation_history_controller():
    """Analyze conversation history and update user preferences"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        conversation_history = data.get('conversation_history')

        if not conversation_history:
            return jsonify({'message': 'Conversation history is required'}), 400

        # Initialize personalization model
        personalization_model = UserPersonalizationModel(user_id)

        # Analyze conversation history
        analysis_results = personalization_model.analyze_conversation_history(conversation_history)

        # Find or create user preferences
        preferences = UserPreference.query.filter_by(user_id=user_id).first()
        if not preferences:
            preferences = UserPreference(user_id=user_id)
            db.session.add(preferences)

        # Update preferences with analysis results
        preferences.typical_sentiment = analysis_results['sentiment']
        preferences.preferred_communication_style = analysis_results['style']
        preferences.frequent_topics = json.dumps(analysis_results['topics'])

        db.session.commit()

        return jsonify(preferences.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        print(f"Analyze conversation history error: {str(e)}")
        return jsonify({'message': 'Server error'}), 500

@jwt_required()
def get_user_profile():
    """Get user profile"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Get user preferences
        preferences = UserPreference.query.filter_by(user_id=user_id).first()
        
        if not preferences:
            preferences = UserPreference(user_id=user_id)
            db.session.add(preferences)
            db.session.commit()
        
        return jsonify({
            'user': user.to_dict(),
            'preferences': preferences.to_dict()
        }), 200
    except Exception as e:
        print(f"Get user profile error: {str(e)}")
        return jsonify({'message': 'Server error'}), 500

@jwt_required()
def update_user_profile():
    """Update user profile"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Check if email is already in use by another user
        if 'email' in data and data['email'] != user.email:
            existing_user = User.query.filter(User.email == data['email'], User.id != user_id).first()
            if existing_user:
                return jsonify({'message': 'Email already in use'}), 400
        
        # Check if username is already in use by another user
        if 'username' in data and data['username'] != user.username:
            existing_user = User.query.filter(User.username == data['username'], User.id != user_id).first()
            if existing_user:
                return jsonify({'message': 'Username already in use'}), 400
        
        # Update user fields
        if 'username' in data:
            user.username = data['username']
        if 'email' in data:
            user.email = data['email']
        if 'theme' in data:
            user.theme = data['theme']
        if 'response_style' in data:
            user.response_style = data['response_style']
        if 'notifications_enabled' in data:
            user.notifications_enabled = data['notifications_enabled']
        
        # If password is provided, update it
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(user.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        print(f"Update user profile error: {str(e)}")
        return jsonify({'message': 'Server error'}), 500

@jwt_required()
def update_user_preferences():
    """Update user preferences"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Find or create user preferences
        preferences = UserPreference.query.filter_by(user_id=user_id).first()
        
        if not preferences:
            preferences = UserPreference(user_id=user_id)
            db.session.add(preferences)
        
        # Update fields if provided
        if 'communication_style' in data:
            preferences.communication_style = data['communication_style']
        
        if 'emotional_state' in data:
            preferences.emotional_state = data['emotional_state']
        
        # Update topics if provided
        if 'topics' in data and isinstance(data['topics'], list):
            # For each topic in the request
            for new_topic_data in data['topics']:
                name = new_topic_data.get('name')
                interest = new_topic_data.get('interest', 5)
                
                if not name:
                    continue
                
                # Check if the topic already exists
                existing_topic = Topic.query.filter_by(
                    preference_id=preferences.id, 
                    name=name
                ).first()
                
                if existing_topic:
                    # Update existing topic
                    existing_topic.interest = interest
                else:
                    # Add new topic
                    new_topic = Topic(
                        preference_id=preferences.id,
                        name=name,
                        interest=interest
                    )
                    db.session.add(new_topic)
        
        # Update last interaction time
        preferences.last_interaction = datetime.utcnow()
        db.session.commit()
        
        return jsonify(preferences.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        print(f"Update user preferences error: {str(e)}")
        return jsonify({'message': 'Server error'}), 500

@jwt_required()
def add_memorized_detail():
    """Add memorized detail for user"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        key = data.get('key')
        value = data.get('value')
        
        if not key or not value:
            return jsonify({'message': 'Key and value are required'}), 400
        
        # Find user preferences
        preferences = UserPreference.query.filter_by(user_id=user_id).first()
        
        if not preferences:
            preferences = UserPreference(user_id=user_id)
            db.session.add(preferences)
            db.session.commit()
        
        # Check if the key already exists
        existing_detail = MemorizedDetail.query.filter_by(
            preference_id=preferences.id,
            key=key
        ).first()
        
        if existing_detail:
            # Update existing detail
            existing_detail.value = value
            existing_detail.timestamp = datetime.utcnow()
        else:
            # Add new detail
            new_detail = MemorizedDetail(
                preference_id=preferences.id,
                key=key,
                value=value
            )
            db.session.add(new_detail)
        
        db.session.commit()
        
        # Get all memorized details
        details = MemorizedDetail.query.filter_by(preference_id=preferences.id).all()
        
        return jsonify([detail.to_dict() for detail in details]), 200
    except Exception as e:
        db.session.rollback()
        print(f"Add memorized detail error: {str(e)}")
        return jsonify({'message': 'Server error'}), 500

@jwt_required()
def get_memorized_details():
    """Get all memorized details for user"""
    try:
        user_id = get_jwt_identity()
        
        # Find user preferences
        preferences = UserPreference.query.filter_by(user_id=user_id).first()
        
        if not preferences:
            return jsonify([]), 200
        
        # Get all memorized details
        details = MemorizedDetail.query.filter_by(preference_id=preferences.id).all()
        
        return jsonify([detail.to_dict() for detail in details]), 200
    except Exception as e:
        print(f"Get memorized details error: {str(e)}")
        return jsonify({'message': 'Server error'}), 500
