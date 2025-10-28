"""
User Personalization Module

This module provides advanced user personalization capabilities:
1. Communication style preferences
2. Topic interest tracking
3. Response customization
4. Behavioral pattern recognition
5. Adaptive interaction
"""

import os
import json
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Union, Tuple
import logging
from pathlib import Path
from datetime import datetime, timedelta
import sys
from collections import Counter

# Add server directory to path to allow imports from other modules
server_dir = Path(__file__).resolve().parent.parent
if str(server_dir) not in sys.path:
    sys.path.append(str(server_dir))

# Import from other modules
from memory.memory_manager import get_memory_manager
from analytics.ml_processor import get_ml_processor
from nlp.sentiment_analysis import analyze_sentiment_and_emotion
from config.advanced_features import USER_PERSONALIZATION_CONFIG, is_feature_enabled

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Base directories
BASE_DIR = server_dir
DATA_DIR = BASE_DIR / "data"
USER_DATA_DIR = DATA_DIR / "user_data"
USER_DATA_DIR.mkdir(exist_ok=True, parents=True)

class UserPersonalization:
    """Class for user personalization and preference management"""
    
    def __init__(self):
        self.memory_manager = get_memory_manager()
        self.ml_processor = get_ml_processor()
        self.user_models = {}  # User-specific models
        
        # Load configuration
        self.config = USER_PERSONALIZATION_CONFIG
        self.enabled = self.config.get("enabled", True)
        self.update_frequency = self.config.get("update_frequency", "message")
        self.personalization_features = self.config.get("features", ["sentiment", "topics", "style"])
        
        # Initialize user style models if enabled
        if "style" in self.personalization_features and is_feature_enabled("ml.user_personalization"):
            self._initialize_style_models()
    
    def _initialize_style_models(self) -> None:
        """Initialize communication style prediction models"""
        try:
            # Get ML processor
            ml_proc = get_ml_processor()
            
            # Check if style prediction model exists
            if "communication_style_predictor" in ml_proc.models:
                logger.info("Communication style predictor model loaded")
            else:
                logger.info("Communication style predictor model not found, will be created when enough data is available")
        except Exception as e:
            logger.error(f"Error initializing style models: {str(e)}")
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get user preferences
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary of user preferences
        """
        try:
            # Get user profile from memory manager
            user_profile = self.memory_manager.get_user_profile(user_id)
            
            # Extract preferences
            preferences = user_profile.profile_data.get("preferences", {})
            
            # Add default preferences if not present
            if "communication_style" not in preferences:
                preferences["communication_style"] = "balanced"
            
            if "response_length" not in preferences:
                preferences["response_length"] = "medium"
            
            if "formality" not in preferences:
                preferences["formality"] = "casual"
            
            return preferences
        except Exception as e:
            logger.error(f"Error getting user preferences: {str(e)}")
            return {
                "communication_style": "balanced",
                "response_length": "medium",
                "formality": "casual"
            }
    
    def update_user_preference(self, user_id: str, preference_key: str, preference_value: Any) -> bool:
        """
        Update a specific user preference
        
        Args:
            user_id: User ID
            preference_key: Preference key to update
            preference_value: New preference value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get user profile from memory manager
            user_profile = self.memory_manager.get_user_profile(user_id)
            
            # Update preference
            user_profile.update_preference(preference_key, preference_value)
            
            return True
        except Exception as e:
            logger.error(f"Error updating user preference: {str(e)}")
            return False
    
    def analyze_user_behavior(self, user_id: str, lookback_days: int = 30) -> Dict[str, Any]:
        """
        Analyze user behavior patterns
        
        Args:
            user_id: User ID
            lookback_days: Number of days to look back for analysis
            
        Returns:
            Dictionary with behavior analysis results
        """
        try:
            # Get hierarchical memory
            h_memory = self.memory_manager.get_hierarchical_memory(user_id)
            
            # Get recent memories
            cutoff_date = datetime.now() - timedelta(days=lookback_days)
            
            # Get all user messages from memory
            user_messages = []
            for memory in h_memory.long_term.items:
                if (memory.source == "conversation:user" and 
                    memory.timestamp >= cutoff_date):
                    user_messages.append({
                        "content": memory.content,
                        "timestamp": memory.timestamp,
                        "metadata": memory.metadata
                    })
            
            # Not enough data
            if len(user_messages) < 5:
                return {
                    "message_count": len(user_messages),
                    "status": "insufficient_data",
                    "recommendation": "Need more interaction data for behavior analysis"
                }
            
            # Analyze message patterns
            df = pd.DataFrame(user_messages)
            
            # Extract hour of day from timestamps
            df["hour"] = df["timestamp"].apply(lambda x: x.hour)
            
            # Count messages by hour
            hour_counts = df["hour"].value_counts().to_dict()
            
            # Determine peak activity hours
            peak_hours = [hour for hour, count in hour_counts.items() 
                          if count >= 0.8 * max(hour_counts.values())]
            
            # Extract topics and sentiments if available
            topics = []
            sentiments = []
            
            for msg in user_messages:
                if "metadata" in msg and msg["metadata"]:
                    if "intent" in msg["metadata"]:
                        topics.append(msg["metadata"]["intent"])
                    
                    if "sentiment" in msg["metadata"]:
                        sentiments.append(msg["metadata"]["sentiment"])
            
            # Count topics and sentiments
            topic_counts = Counter(topics)
            sentiment_counts = Counter(sentiments)
            
            # Determine favorite topics
            favorite_topics = [topic for topic, count in topic_counts.most_common(3)]
            
            # Determine dominant sentiment
            dominant_sentiment = sentiment_counts.most_common(1)[0][0] if sentiment_counts else "neutral"
            
            # Compile results
            results = {
                "message_count": len(user_messages),
                "peak_activity_hours": peak_hours,
                "favorite_topics": favorite_topics,
                "dominant_sentiment": dominant_sentiment,
                "topic_distribution": {k: v / len(topics) for k, v in topic_counts.items()} if topics else {},
                "sentiment_distribution": {k: v / len(sentiments) for k, v in sentiment_counts.items()} if sentiments else {},
                "status": "success"
            }
            
            return results
        except Exception as e:
            logger.error(f"Error analyzing user behavior: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def predict_communication_style(self, user_id: str, message_text: str) -> Dict[str, Any]:
        """
        Predict preferred communication style based on user message
        
        Args:
            user_id: User ID
            message_text: User message text
            
        Returns:
            Dictionary with predicted communication style
        """
        try:
            # Default style if prediction fails
            default_style = {
                "communication_style": "balanced",
                "confidence": 0.5,
                "method": "default"
            }
            
            # Check if style prediction is enabled
            if "style" not in self.personalization_features:
                return default_style
            
            # Get user profile
            user_profile = self.memory_manager.get_user_profile(user_id)
            
            # Check if user has explicitly set a preference
            explicit_style = user_profile.get_preference("communication_style")
            if explicit_style:
                return {
                    "communication_style": explicit_style,
                    "confidence": 1.0,
                    "method": "explicit_preference"
                }
            
            # Analyze message sentiment
            sentiment_analysis = analyze_sentiment_and_emotion(message_text)
            
            # Simple rule-based style prediction
            sentiment = sentiment_analysis["dominant_sentiment"]
            emotion = sentiment_analysis["dominant_emotion"]
            
            if sentiment == "negative":
                if emotion in ["anger", "disgust"]:
                    style = "concise"  # Keep it brief for angry users
                else:
                    style = "empathetic"  # Be supportive for sad/fearful users
                confidence = 0.7
                method = "sentiment_rule"
            elif sentiment == "positive":
                if emotion == "joy":
                    style = "friendly"  # Be upbeat for happy users
                else:
                    style = "balanced"  # Balanced for positive but not joyful
                confidence = 0.7
                method = "sentiment_rule"
            else:
                # Try ML prediction if available
                ml_proc = get_ml_processor()
                if "communication_style_predictor" in ml_proc.models:
                    # Prepare features for prediction
                    features = {
                        "message_text": message_text,
                        "sentiment": sentiment,
                        "emotion": emotion
                    }
                    
                    # Make prediction
                    prediction = ml_proc.predict(features, "communication_style_predictor")
                    
                    if "error" not in prediction and prediction.get("predictions"):
                        pred = prediction["predictions"][0]
                        style = pred["prediction"]
                        confidence = max(pred.get("probabilities", {}).values()) if pred.get("probabilities") else 0.6
                        method = "ml_model"
                    else:
                        style = "balanced"
                        confidence = 0.5
                        method = "default"
                else:
                    style = "balanced"
                    confidence = 0.5
                    method = "default"
            
            return {
                "communication_style": style,
                "confidence": confidence,
                "method": method
            }
        except Exception as e:
            logger.error(f"Error predicting communication style: {str(e)}")
            return {
                "communication_style": "balanced",
                "confidence": 0.5,
                "method": "default"
            }
    
    def track_topic_interest(self, user_id: str, message_text: str, intent: str) -> Dict[str, Any]:
        """
        Track user interest in topics
        
        Args:
            user_id: User ID
            message_text: User message text
            intent: Detected intent
            
        Returns:
            Dictionary with updated topic interests
        """
        try:
            # Check if topic tracking is enabled
            if "topics" not in self.personalization_features:
                return {"status": "disabled"}
            
            # Get user profile
            user_profile = self.memory_manager.get_user_profile(user_id)
            
            # Record message with topic
            user_profile.record_message(topic=intent)
            
            # Get updated favorite topics
            favorite_topics = user_profile.get_favorite_topics()
            
            return {
                "status": "success",
                "favorite_topics": favorite_topics
            }
        except Exception as e:
            logger.error(f"Error tracking topic interest: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def customize_response(self, response_text: str, user_id: str, style_preference: Dict[str, Any] = None) -> str:
        """
        Customize response based on user preferences
        
        Args:
            response_text: Original response text
            user_id: User ID
            style_preference: Style preference (if already determined)
            
        Returns:
            Customized response text
        """
        try:
            # Get user preferences
            preferences = self.get_user_preferences(user_id)
            
            # Get communication style
            if style_preference:
                style = style_preference.get("communication_style", "balanced")
            else:
                style = preferences.get("communication_style", "balanced")
            
            # Get response length preference
            length_pref = preferences.get("response_length", "medium")
            
            # Get formality preference
            formality = preferences.get("formality", "casual")
            
            # Apply customizations based on preferences
            customized_response = response_text
            
            # Adjust for communication style
            if style == "empathetic":
                # Add empathetic phrases if not already present
                empathetic_phrases = [
                    "I understand", "I see how you feel", "That sounds", "I appreciate"
                ]
                
                if not any(phrase in customized_response for phrase in empathetic_phrases):
                    customized_response = f"I understand. {customized_response}"
            
            elif style == "concise":
                # Shorten response by removing unnecessary phrases
                filler_phrases = [
                    "I think that ", "It seems like ", "You know, ", "Basically, ",
                    "In my opinion, ", "As I see it, ", "To be honest, "
                ]
                
                for phrase in filler_phrases:
                    customized_response = customized_response.replace(phrase, "")
                
                # Split into sentences and keep only the most important ones
                sentences = customized_response.split(". ")
                if len(sentences) > 3:
                    customized_response = ". ".join(sentences[:3]) + "."
            
            elif style == "friendly":
                # Add friendly elements if not already present
                if not any(x in customized_response for x in ["!", "Great", "Wonderful", "Nice"]):
                    customized_response = f"{customized_response} Hope that helps!"
            
            elif style == "professional":
                # Make more formal and structured
                customized_response = customized_response.replace("don't", "do not")
                customized_response = customized_response.replace("can't", "cannot")
                customized_response = customized_response.replace("I'm", "I am")
                customized_response = customized_response.replace("you're", "you are")
            
            # Adjust for length preference
            if length_pref == "short" and len(customized_response) > 100:
                # Shorten by keeping only first and last sentences
                sentences = customized_response.split(". ")
                if len(sentences) > 2:
                    customized_response = f"{sentences[0]}. {sentences[-1]}"
            
            elif length_pref == "long" and len(customized_response) < 200:
                # This would ideally expand the response, but for now we'll leave it
                # as expanding requires more complex NLG capabilities
                pass
            
            # Adjust for formality
            if formality == "formal":
                # Replace casual phrases with formal ones
                casual_to_formal = {
                    "yeah": "yes",
                    "nope": "no",
                    "kinda": "somewhat",
                    "a lot": "significantly",
                    "awesome": "excellent",
                    "huge": "substantial",
                    "okay": "acceptable",
                    "OK": "acceptable",
                    "sure": "certainly",
                    "thanks": "thank you",
                    "hi": "hello"
                }
                
                for casual, formal in casual_to_formal.items():
                    customized_response = customized_response.replace(f" {casual} ", f" {formal} ")
            
            elif formality == "casual" and style != "friendly":
                # Already handled by friendly style, so only apply if not friendly
                if not any(x in customized_response for x in ["!", "?"]):
                    customized_response = f"{customized_response} 👍"
            
            return customized_response
        except Exception as e:
            logger.error(f"Error customizing response: {str(e)}")
            return response_text  # Return original if customization fails
    
    def update_user_model(self, user_id: str, message_text: str, user_response: Dict[str, Any]) -> bool:
        """
        Update user model based on new interaction
        
        Args:
            user_id: User ID
            message_text: User message text
            user_response: User response data including intent, sentiment, etc.
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if model updating is enabled
            if not self.enabled or self.update_frequency == "none":
                return False
            
            # Check if we should update based on frequency
            if self.update_frequency == "session":
                # Only update once per session
                user_profile = self.memory_manager.get_user_profile(user_id)
                last_update = user_profile.get_preference("last_model_update")
                
                if last_update:
                    last_update_time = datetime.fromisoformat(last_update)
                    if (datetime.now() - last_update_time).total_seconds() < 3600:  # Within an hour
                        return False
            
            elif self.update_frequency == "daily":
                # Only update once per day
                user_profile = self.memory_manager.get_user_profile(user_id)
                last_update = user_profile.get_preference("last_model_update")
                
                if last_update:
                    last_update_time = datetime.fromisoformat(last_update)
                    if (datetime.now() - last_update_time).days < 1:
                        return False
            
            # Get ML processor
            ml_proc = get_ml_processor()
            
            # Update communication style model if enabled
            if "style" in self.personalization_features:
                # Check if we have enough data to train/update the model
                style_data_file = USER_DATA_DIR / "communication_style_data.json"
                
                # Load existing data if available
                style_data = []
                if style_data_file.exists():
                    try:
                        with open(style_data_file, "r", encoding="utf-8") as f:
                            style_data = json.load(f)
                    except:
                        style_data = []
                
                # Extract features from current message
                sentiment_analysis = analyze_sentiment_and_emotion(message_text)
                
                # Determine style label (using current preference as proxy for what worked)
                user_profile = self.memory_manager.get_user_profile(user_id)
                style_label = user_profile.get_preference("communication_style", "balanced")
                
                # Create new data point
                new_data_point = {
                    "message_text": message_text,
                    "sentiment": sentiment_analysis["dominant_sentiment"],
                    "emotion": sentiment_analysis["dominant_emotion"],
                    "intent": user_response.get("intent", ""),
                    "style_label": style_label,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Add to dataset
                style_data.append(new_data_point)
                
                # Save updated dataset
                style_data_file.parent.mkdir(exist_ok=True, parents=True)
                with open(style_data_file, "w", encoding="utf-8") as f:
                    json.dump(style_data, f, indent=2)
                
                # Train/update model if we have enough data
                if len(style_data) >= 20:
                    # Prepare training data
                    df = pd.DataFrame(style_data)
                    
                    # Simple feature extraction
                    X = pd.DataFrame({
                        "sentiment_numeric": df["sentiment"].map({"positive": 1, "neutral": 0, "negative": -1}),
                        "emotion_joy": df["emotion"].apply(lambda x: 1 if x == "joy" else 0),
                        "emotion_sadness": df["emotion"].apply(lambda x: 1 if x == "sadness" else 0),
                        "emotion_anger": df["emotion"].apply(lambda x: 1 if x == "anger" else 0),
                        "emotion_fear": df["emotion"].apply(lambda x: 1 if x == "fear" else 0),
                        "emotion_surprise": df["emotion"].apply(lambda x: 1 if x == "surprise" else 0)
                    })
                    
                    y = df["style_label"]
                    
                    # Train model
                    ml_proc.train_classifier(
                        X, y,
                        model_type="random_forest",
                        model_name="communication_style_predictor",
                        save_model=True
                    )
            
            # Record update time
            user_profile = self.memory_manager.get_user_profile(user_id)
            user_profile.update_preference("last_model_update", datetime.now().isoformat())
            
            return True
        except Exception as e:
            logger.error(f"Error updating user model: {str(e)}")
            return False
    
    def get_personalized_context(self, user_id: str, message_text: str = None) -> Dict[str, Any]:
        """
        Get personalized context for response generation
        
        Args:
            user_id: User ID
            message_text: Current user message text (optional)
            
        Returns:
            Dictionary with personalized context
        """
        try:
            # Get user profile
            user_profile = self.memory_manager.get_user_profile(user_id)
            
            # Get preferences
            preferences = self.get_user_preferences(user_id)
            
            # Get favorite topics
            favorite_topics = user_profile.get_favorite_topics()
            
            # Predict communication style if message provided
            style_prediction = None
            if message_text:
                style_prediction = self.predict_communication_style(user_id, message_text)
            
            # Get behavior analysis
            behavior = self.analyze_user_behavior(user_id)
            
            # Compile personalized context
            context = {
                "user_id": user_id,
                "preferences": preferences,
                "favorite_topics": favorite_topics,
                "communication_style": style_prediction["communication_style"] if style_prediction else preferences.get("communication_style", "balanced"),
                "behavior_patterns": {
                    "peak_activity_hours": behavior.get("peak_activity_hours", []),
                    "dominant_sentiment": behavior.get("dominant_sentiment", "neutral"),
                    "favorite_topics": behavior.get("favorite_topics", [])
                },
                "personal_info": user_profile.profile_data.get("personal_info", {})
            }
            
            return context
        except Exception as e:
            logger.error(f"Error getting personalized context: {str(e)}")
            return {
                "user_id": user_id,
                "preferences": {
                    "communication_style": "balanced",
                    "response_length": "medium",
                    "formality": "casual"
                }
            }

# Create a global instance
user_personalization = UserPersonalization()

def get_user_personalization() -> UserPersonalization:
    """Get the global user personalization instance"""
    return user_personalization


# Backwards-compatible alias expected by the rest of the codebase
class UserPersonalizationEngine(UserPersonalization):
    def __init__(self, config: Dict[str, Any] = None, memory_manager=None, ml_processor=None):
        # Initialize base functionality
        super().__init__()
        self.config = config or {}
        if memory_manager is not None:
            self.memory_manager = memory_manager
        if ml_processor is not None:
            self.ml_processor = ml_processor

    # Provide a similar public API as UserPersonalization
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        return super().get_user_preferences(user_id)

    def update_user_preference(self, user_id: str, preference_key: str, preference_value: Any) -> bool:
        return super().update_user_preference(user_id, preference_key, preference_value)

    def get_personalized_context(self, user_id: str, message_text: str = None) -> Dict[str, Any]:
        return super().get_personalized_context(user_id, message_text)
