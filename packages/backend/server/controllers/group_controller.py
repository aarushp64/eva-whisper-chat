from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.db import db
from models.group import Group
from models.group_member import GroupMember
from models.user import User
from models.chat import Chat
from datetime import datetime

@jwt_required()
def create_group():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        name = data.get('name')
        description = data.get('description', '')

        if not name:
            return jsonify({'message': 'Group name is required'}), 400

        # Check if group name already exists
        existing_group = Group.query.filter_by(name=name).first()
        if existing_group:
            return jsonify({'message': 'Group with this name already exists'}), 400

        new_group = Group(name=name, description=description, created_by=user_id)
        db.session.add(new_group)
        db.session.commit()

        # Add creator as a member
        creator_member = GroupMember(group_id=new_group.id, user_id=user_id)
        db.session.add(creator_member)
        db.session.commit()

        # Create a chat associated with this group
        group_chat = Chat(group_id=new_group.id, chat_type='group', title=f"Group Chat: {name}")
        db.session.add(group_chat)
        db.session.commit()

        return jsonify(new_group.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        print(f"Create group error: {str(e)}")
        return jsonify({'message': 'Server error'}), 500

@jwt_required()
def invite_user_to_group():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        group_id = data.get('group_id')
        invited_user_id = data.get('user_id')

        if not group_id or not invited_user_id:
            return jsonify({'message': 'Group ID and User ID are required'}), 400

        group = Group.query.get(group_id)
        if not group:
            return jsonify({'message': 'Group not found'}), 404

        # Check if the inviting user is a member of the group (optional: check if admin/creator)
        is_member = GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first()
        if not is_member:
            return jsonify({'message': 'You are not authorized to invite users to this group'}), 403

        # Check if invited user exists
        invited_user = User.query.get(invited_user_id)
        if not invited_user:
            return jsonify({'message': 'Invited user not found'}), 404

        # Check if user is already a member
        already_member = GroupMember.query.filter_by(group_id=group_id, user_id=invited_user_id).first()
        if already_member:
            return jsonify({'message': 'User is already a member of this group'}), 400

        new_member = GroupMember(group_id=group_id, user_id=invited_user_id)
        db.session.add(new_member)
        db.session.commit()

        return jsonify({'message': 'User invited to group successfully'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Invite user to group error: {str(e)}")
        return jsonify({'message': 'Server error'}), 500

@jwt_required()
def get_user_groups():
    try:
        user_id = get_jwt_identity()
        member_entries = GroupMember.query.filter_by(user_id=user_id).all()
        group_ids = [entry.group_id for entry in member_entries]
        
        groups = Group.query.filter(Group.id.in_(group_ids)).all()
        return jsonify([group.to_dict() for group in groups]), 200
    except Exception as e:
        print(f"Get user groups error: {str(e)}")
        return jsonify({'message': 'Server error'}), 500

@jwt_required()
def get_group_members(group_id):
    try:
        user_id = get_jwt_identity()
        
        # Check if user is a member of the group
        is_member = GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first()
        if not is_member:
            return jsonify({'message': 'You are not a member of this group'}), 403

        members = GroupMember.query.filter_by(group_id=group_id).all()
        member_user_ids = [member.user_id for member in members]
        
        users = User.query.filter(User.id.in_(member_user_ids)).all()
        return jsonify([user.to_dict() for user in users]), 200
    except Exception as e:
        print(f"Get group members error: {str(e)}")
        return jsonify({'message': 'Server error'}), 500

@jwt_required()
def get_group_chat_messages(group_id):
    try:
        user_id = get_jwt_identity()
        
        # Check if user is a member of the group
        is_member = GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first()
        if not is_member:
            return jsonify({'message': 'You are not a member of this group'}), 403

        # Find the chat associated with this group
        group_chat = Chat.query.filter_by(group_id=group_id, chat_type='group').first()
        if not group_chat:
            return jsonify({'message': 'Group chat not found'}), 404

        messages = group_chat.messages.order_by(Message.timestamp.asc()).all()
        return jsonify([message.to_dict() for message in messages]), 200
    except Exception as e:
        print(f"Get group chat messages error: {str(e)}")
        return jsonify({'message': 'Server error'}), 500
