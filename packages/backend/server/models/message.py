from models.db import db
from datetime import datetime

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chats.id'), nullable=False)
    sender = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    sentiment = db.Column(db.String(20), default='neutral')  # 'positive', 'negative', 'neutral'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert message object to dictionary"""
        return {
            'id': self.id,
            'chat_id': self.chat_id,
            'sender': self.sender,
            'content': self.content,
            'sentiment': self.sentiment,
            'timestamp': self.timestamp.isoformat()
        }
