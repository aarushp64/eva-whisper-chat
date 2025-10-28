from models.db import db
from datetime import datetime

class Chat(db.Model):
    __tablename__ = 'chats'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # Nullable for group chats
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=True) # Link to group
    title = db.Column(db.String(100), default='New Conversation')
    chat_type = db.Column(db.String(20), default='private', nullable=False) # 'private' or 'group'
    last_message = db.Column(db.String(500), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = db.relationship('Message', backref='chat', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert chat object to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'last_message': self.last_message,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
