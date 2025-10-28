from models.db import db
from datetime import datetime
import json

class MemorizedDetail(db.Model):
    __tablename__ = 'memorized_details'
    
    id = db.Column(db.Integer, primary_key=True)
    preference_id = db.Column(db.Integer, db.ForeignKey('user_preferences.id'), nullable=False)
    key = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'timestamp': self.timestamp.isoformat()
        }

class Topic(db.Model):
    __tablename__ = 'topics'
    
    id = db.Column(db.Integer, primary_key=True)
    preference_id = db.Column(db.Integer, db.ForeignKey('user_preferences.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    interest = db.Column(db.Integer, default=5)  # 1-10 scale
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'interest': self.interest
        }

class UserPreference(db.Model):
    __tablename__ = 'user_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    communication_style = db.Column(db.String(20), default='empathetic')  # 'casual', 'formal', 'empathetic', 'concise', 'humorous'
    preferred_communication_style = db.Column(db.String(50), default='unknown')
    typical_sentiment = db.Column(db.String(50), default='unknown')
    frequent_topics = db.Column(db.Text)
    emotional_state = db.Column(db.String(20), default='unknown')  # 'happy', 'sad', 'neutral', 'excited', 'anxious', 'unknown'
    last_interaction = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    topics = db.relationship('Topic', backref='preference', lazy=True, cascade='all, delete-orphan')
    memorized_details = db.relationship('MemorizedDetail', backref='preference', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert user preference object to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'communication_style': self.communication_style,
            'preferred_communication_style': self.preferred_communication_style,
            'typical_sentiment': self.typical_sentiment,
            'frequent_topics': json.loads(self.frequent_topics) if self.frequent_topics else [],
            'emotional_state': self.emotional_state,
            'last_interaction': self.last_interaction.isoformat(),
            'topics': [topic.to_dict() for topic in self.topics],
            'memorized_details': [detail.to_dict() for detail in self.memorized_details]
        }
