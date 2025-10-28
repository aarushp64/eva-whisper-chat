from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.db import db
from models.chat import Chat
from models.message import Message
from models.user import User
from datetime import datetime
from memory.memory_manager import get_memory_manager
from nlp.sentiment_analysis import analyze_sentiment
from ml.user_personalization import UserPersonalizationModel

memory_manager = get_memory_manager()

@jwt_required()
def get_chats():
    """Get all chats for a user"""
    try:
        user_id = get_jwt_identity()
        chats = Chat.query.filter_by(user_id=user_id).order_by(Chat.updated_at.desc()).all()
        return jsonify([chat.to_dict() for chat in chats]), 200
    except Exception as e:
        print(f"Get chats error: {str(e)}")
        return jsonify({'message': 'Server error'}), 500

@jwt_required()
def create_chat():
    """Create a new chat"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        title = data.get('title', 'New Conversation')
        
        # Create new chat
        new_chat = Chat(user_id=user_id, title=title)
        db.session.add(new_chat)
        db.session.commit()
        
        # Add initial greeting message from EVA
        welcome_message = Message(
            chat_id=new_chat.id,
            sender='assistant',
            content="Hi, I'm EVA! How can I assist you today?",
            sentiment='positive'
        )
        db.session.add(welcome_message)
        
        # Update the chat with the last message
        new_chat.last_message = welcome_message.content
        new_chat.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(new_chat.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        print(f"Create chat error: {str(e)}")
        return jsonify({'message': 'Server error'}), 500

@jwt_required()
def get_chat_by_id(chat_id):
    """Get a single chat by ID"""
    try:
        user_id = get_jwt_identity()
        chat = Chat.query.filter_by(id=chat_id, user_id=user_id).first()
        
        if not chat:
            return jsonify({'message': 'Chat not found'}), 404
        
        return jsonify(chat.to_dict()), 200
    except Exception as e:
        print(f"Get chat by ID error: {str(e)}")
        return jsonify({'message': 'Server error'}), 500

@jwt_required()
def update_chat(chat_id):
    """Update chat title"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        title = data.get('title')
        
        if not title:
            return jsonify({'message': 'Title is required'}), 400
        
        chat = Chat.query.filter_by(id=chat_id, user_id=user_id).first()
        
        if not chat:
            return jsonify({'message': 'Chat not found'}), 404
        
        chat.title = title
        chat.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(chat.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        print(f"Update chat error: {str(e)}")
        return jsonify({'message': 'Server error'}), 500

@jwt_required()
def delete_chat(chat_id):
    """Delete a chat"""
    try:
        user_id = get_jwt_identity()
        chat = Chat.query.filter_by(id=chat_id, user_id=user_id).first()
        
        if not chat:
            return jsonify({'message': 'Chat not found'}), 404
        
        # Delete the chat (cascade will delete messages)
        db.session.delete(chat)
        db.session.commit()
        
        return jsonify({'message': 'Chat deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Delete chat error: {str(e)}")
        return jsonify({'message': 'Server error'}), 500

@jwt_required()
def get_chat_messages(chat_id):
    """Get all messages for a chat"""
    try:
        user_id = get_jwt_identity()
        
        # First verify the chat belongs to the user
        chat = Chat.query.filter_by(id=chat_id, user_id=user_id).first()
        
        if not chat:
            return jsonify({'message': 'Chat not found'}), 404
        
        messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp.asc()).all()
        
        return jsonify([message.to_dict() for message in messages]), 200
    except Exception as e:
        print(f"Get chat messages error: {str(e)}")
        return jsonify({'message': 'Server error'}), 500

@jwt_required()
def handle_chat_message(chat_id):
    """Handle incoming chat messages, retrieve context, and generate AI response"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        user_message_content = data.get('message')

        if not user_message_content:
            return jsonify({'message': 'Message content is required'}), 400

        # Verify the chat belongs to the user
        chat = Chat.query.filter_by(id=chat_id, user_id=user_id).first()
        if not chat:
            return jsonify({'message': 'Chat not found'}), 404

        # 1. Store user's message in conversation memory
        user_message = {
            "sender": "user",
            "content": user_message_content,
            "timestamp": datetime.utcnow().isoformat()
        }
        memory_manager.add_conversation_message(user_id, user_message, chat_id)

        # Analyze sentiment of the user's message
        sentiment_score = analyze_sentiment(user_message_content)
        user_message["sentiment"] = sentiment_score

        # Get conversation topic (simplified for now, can be enhanced with NLP topic modeling)
        # For now, we'll use the user personalization model's topic clustering if available
        personalization_model = UserPersonalizationModel.load(user_id)
        personalization_model.add_message(user_message) # Add message to history for topic clustering
        
        conversation_topic = "general"
        if len(personalization_model.message_history) > 5: # Need some history for clustering
            topic_clusters = personalization_model.cluster_topics(n_clusters=1) # Try to get a dominant topic
            if topic_clusters and topic_clusters["cluster_summaries"]:
                # Get the top terms of the most dominant cluster as the topic
                dominant_cluster_id = list(topic_clusters["cluster_summaries"].keys())[0]
                conversation_topic = topic_clusters["cluster_summaries"][dominant_cluster_id]["top_terms"][0]
        
        user_message["topic"] = conversation_topic
        personalization_model.save() # Save updated message history and potential topic clusters

        # 2. Retrieve relevant contextual memories
        contextual_memories = memory_manager.get_contextual_memories(user_id, user_message_content, chat_id)

        # 3. Construct prompt for AI (simplified for now)
        prompt = f"User: {user_message_content}\n\n"
        if contextual_memories.get("recent_conversation"):
            prompt += "Recent Conversation:\n"
            for msg in contextual_memories["recent_conversation"]:
                prompt += f"  {msg['sender']}: {msg['content']}\n"
        if contextual_memories.get("hierarchical_memories"):
            prompt += "\nRelevant Memories:\n"
            for mem in contextual_memories["hierarchical_memories"]:
                prompt += f"  - {mem['content']} (Source: {mem['source']})\n"
        if contextual_memories.get("user_profile"):
            prompt += f"\nUser Profile: {contextual_memories['user_profile']}\n"
        if contextual_memories.get("knowledge_base_entities"):
            prompt += f"\nKnowledge Base Entities: {contextual_memories['knowledge_base_entities']}\n"
        
        # Placeholder for AI response generation
        ai_response_content = f"AI response to: {user_message_content}. Sentiment: {sentiment_score}. Topic: {conversation_topic}. Context used: {len(contextual_memories.get('hierarchical_memories', []))} memories, {len(contextual_memories.get('knowledge_base_entities', []))} KB entities."

        # 4. Store AI's response in conversation memory
        ai_message = {
            "sender": "assistant",
            "content": ai_response_content,
            "timestamp": datetime.utcnow().isoformat(),
            "sentiment": analyze_sentiment(ai_response_content) # Analyze sentiment of AI response
        }
        memory_manager.add_conversation_message(user_id, ai_message, chat_id)

        # 5. Trigger memory consolidation (asynchronously or periodically in a real system)
        memory_manager.consolidate_memory(user_id, chat_id)

        # Update chat's last message and updated_at
        chat.last_message = ai_message["content"]
        chat.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            "response": ai_response_content,
            "sentiment_score": sentiment_score,
            "conversation_topic": conversation_topic
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Handle chat message error: {str(e)}")
        return jsonify({'message': 'Server error'}), 500
