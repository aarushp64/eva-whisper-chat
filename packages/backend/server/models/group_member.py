from models.db import db
from datetime import datetime

class GroupMember(db.Model):
    __tablename__ = 'group_members'
    
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Define a unique constraint to prevent duplicate members in a group
    __table_args__ = (db.UniqueConstraint('group_id', 'user_id', name='_group_user_uc'),)

    def to_dict(self):
        return {
            'id': self.id,
            'group_id': self.group_id,
            'user_id': self.user_id,
            'joined_at': self.joined_at.isoformat()
        }
