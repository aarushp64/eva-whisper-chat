from models.db import db
from models.user_preference import UserPreference
from utils.sentiment_analysis import analyze_user_sentiment, get_emotional_intensity
from datetime import datetime
import re

def update_user_emotional_state(user_id, sentiment, message_content):
    """
    Update the user's emotional state based on message content and sentiment
    """
    try:
        # Find user preferences
        preferences = UserPreference.query.filter_by(user_id=user_id).first()
        
        if not preferences:
            preferences = UserPreference(user_id=user_id)
            db.session.add(preferences)
        
        # Get emotional intensity
        intensity = get_emotional_intensity(message_content)
        
        # Only update emotional state if the message has significant emotional content
        if intensity > 0.3:
            # Map sentiment to emotional state
            if sentiment == 'positive':
                if intensity > 0.6:
                    preferences.emotional_state = 'excited'
                else:
                    preferences.emotional_state = 'happy'
            elif sentiment == 'negative':
                if intensity > 0.6:
                    preferences.emotional_state = 'anxious'
                else:
                    preferences.emotional_state = 'sad'
            else:
                preferences.emotional_state = 'neutral'
        
        # Update last interaction time
        preferences.last_interaction = datetime.utcnow()
        db.session.commit()
        
        return preferences.emotional_state
    except Exception as e:
        db.session.rollback()
        print(f"Error updating user emotional state: {str(e)}")
        return 'unknown'

def detect_user_interests(message_content):
    """
    Detect potential user interests from message content
    Returns a list of potential topics of interest
    """
    # Simple keyword-based interest detection
    interest_keywords = {
        'technology': ['tech', 'computer', 'software', 'hardware', 'programming', 'code', 'app', 'digital'],
        'health': ['health', 'fitness', 'exercise', 'diet', 'nutrition', 'workout', 'wellness'],
        'entertainment': ['movie', 'film', 'tv', 'show', 'music', 'concert', 'book', 'novel', 'game'],
        'travel': ['travel', 'trip', 'vacation', 'journey', 'tour', 'visit', 'country', 'city'],
        'food': ['food', 'cook', 'recipe', 'meal', 'restaurant', 'dish', 'cuisine'],
        'education': ['learn', 'study', 'school', 'college', 'university', 'course', 'education'],
        'finance': ['money', 'finance', 'investment', 'stock', 'budget', 'saving', 'expense'],
        'sports': ['sport', 'team', 'player', 'match', 'game', 'competition', 'tournament']
    }
    
    detected_interests = []
    message_lower = message_content.lower()
    
    for interest, keywords in interest_keywords.items():
        for keyword in keywords:
            # Use word boundary to match whole words
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, message_lower):
                detected_interests.append(interest)
                break  # Only add each interest once
    
    return detected_interests

def update_user_interests(user_id, message_content):
    """
    Update user interests based on message content
    """
    try:
        # Detect interests from message
        detected_interests = detect_user_interests(message_content)
        
        if not detected_interests:
            return
        
        # Find user preferences
        preferences = UserPreference.query.filter_by(user_id=user_id).first()
        
        if not preferences:
            preferences = UserPreference(user_id=user_id)
            db.session.add(preferences)
            db.session.commit()
        
        # Update interests
        for interest in detected_interests:
            # Check if interest already exists
            existing_topic = next((t for t in preferences.topics if t.name == interest), None)
            
            if existing_topic:
                # Increase interest level (max 10)
                existing_topic.interest = min(existing_topic.interest + 1, 10)
            else:
                # Add new topic with default interest level
                new_topic = Topic(preference_id=preferences.id, name=interest, interest=5)
                db.session.add(new_topic)
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error updating user interests: {str(e)}")

# Import here to avoid circular imports
from models.user_preference import Topic
