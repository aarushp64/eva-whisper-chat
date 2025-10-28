from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
import base64
from models.db import db
from models.message import Message
from models.chat import Chat
from models.user_preference import UserPreference, MemorizedDetail
from utils.sentiment_analysis import analyze_user_sentiment
from utils.response_generator import generate_response
from utils.user_profiling import update_user_emotional_state
from utils.memory_manager import extract_key_information
# from speech.speech_integration import SpeechIntegration
from datetime import datetime

def handle_message(data):
    """Handle incoming message and generate response"""
    try:
        # Extract message data
        chat_id = data.get('chatId') or data.get('chat_id')
        content = data.get('content')
        user_id = data.get('userId') or data.get('user_id')
        is_audio = data.get('is_audio', False)
        audio_metadata = data.get('audio_metadata', {})
        
        # Check if this is an audio message that needs processing
        if is_audio and 'audio_base64' in data:
            return handle_audio_message(data)
        
        # Analyze user sentiment - use the more advanced analyzer if available
        try:
            sentiment_analysis = analyze_sentiment_and_emotion(content)
            sentiment = sentiment_analysis['dominant_sentiment']
        except Exception:
            # Fallback to simpler sentiment analysis
            sentiment = analyze_user_sentiment(content)
        
        # Save user message with metadata
        metadata = {}
        if is_audio:
            metadata['is_audio'] = True
            metadata.update(audio_metadata)
        
        user_message = Message(
            chat_id=chat_id,
            sender='user',
            content=content,
            sentiment=sentiment,
            metadata=json.dumps(metadata)
        )
        db.session.add(user_message)
        
        # Update chat's last message and timestamp
        chat = Chat.query.get(chat_id)
        if chat:
            chat.last_message = content
            chat.updated_at = datetime.utcnow()
            db.session.commit()
        
        # Update user emotional state based on message content
        update_user_emotional_state(user_id, sentiment, content)
        
        # Extract and store any key information from the message
        extract_key_information(user_id, content)
        
        # Get user preferences to personalize response
        user_preference = UserPreference.query.filter_by(user_id=user_id).first()
        
        # Generate EVA's response - use enhanced response generator with context
        context = {
            'user_id': user_id,
            'chat_id': chat_id,
            'is_audio': is_audio
        }
        
        response_data = generate_response(content, user_preference, sentiment, context)
        
        # Extract response content and metadata
        if isinstance(response_data, dict) and 'text' in response_data:
            response_content = response_data['text']
            response_metadata = response_data.get('metadata', {})
        else:
            # Handle legacy response format (string only)
            response_content = response_data
            response_metadata = {}
        
        # Save EVA's response with metadata
        assistant_message = Message(
            chat_id=chat_id,
            sender='assistant',
            content=response_content,
            sentiment=response_metadata.get('sentiment', 'neutral'),
            metadata=json.dumps(response_metadata)
        )
        db.session.add(assistant_message)
        
        # Update chat's last message again
        if chat:
            chat.last_message = response_content
            chat.updated_at = datetime.utcnow()
            db.session.commit()
        
        # Prepare response object
        response = {
            'message': assistant_message.to_dict(),
            'userMessage': user_message.to_dict()
        }
        
        # Add any additional metadata from the response generator
        if isinstance(response_data, dict) and 'metadata' in response_data:
            response['metadata'] = response_data['metadata']
        
        return response
    except Exception as e:
        db.session.rollback()
        print(f"Handle message error: {str(e)}")
        raise e

def handle_audio_message(data):
    """Handle incoming audio message and generate response"""
    try:
        # Extract audio data
        chat_id = data.get('chatId') or data.get('chat_id')
        user_id = data.get('userId') or data.get('user_id')
        audio_base64 = data.get('audio_base64')
        audio_format = data.get('audio_format', 'wav')
        language = data.get('language')
        tts_enabled = data.get('tts_enabled', True)
        voice_id = data.get('voice_id', '21m00Tcm4TlvDq8ikWAM')
        
        if not audio_base64:
            raise ValueError("Missing audio data")
        
        # Get user preferences
        user_preference = UserPreference.query.filter_by(user_id=user_id).first()
        
        # Process audio message using speech integration
        speech_integration = SpeechIntegration(user_id=user_id)
        result = speech_integration.process_audio_message(
            audio_base64=audio_base64,
            audio_format=audio_format,
            language=language,
            user_preference=user_preference,
            chat_id=chat_id,
            tts_enabled=tts_enabled,
            voice_id=voice_id
        )
        
        if "error" in result:
            raise ValueError(result["error"])
        
        # Extract transcription and response
        transcription = result["transcription"]
        response = result["response"]
        
        # Save user message with transcription
        user_message = Message(
            chat_id=chat_id,
            sender='user',
            content=transcription["text"],
            sentiment=response["metadata"].get("sentiment", "neutral"),
            metadata=json.dumps({
                "is_audio": True,
                "language": transcription.get("language"),
                "timestamp": transcription.get("timestamp")
            })
        )
        db.session.add(user_message)
        
        # Save EVA's response
        assistant_message = Message(
            chat_id=chat_id,
            sender='assistant',
            content=response["text"],
            sentiment=response["metadata"].get("sentiment", "neutral"),
            metadata=json.dumps(response["metadata"])
        )
        db.session.add(assistant_message)
        
        # Update chat's last message and timestamp
        chat = Chat.query.get(chat_id)
        if chat:
            chat.last_message = response["text"]
            chat.updated_at = datetime.utcnow()
            db.session.commit()
        
        # Prepare response object
        response_obj = {
            'message': assistant_message.to_dict(),
            'userMessage': user_message.to_dict(),
            'transcription': transcription,
            'metadata': response["metadata"]
        }
        
        # Add audio response if available
        if "audio_response" in result:
            response_obj["audio_response"] = result["audio_response"]["audio_base64"]
            response_obj["audio_format"] = result["audio_response"]["format"]
        
        return response_obj
        
    except Exception as e:
        db.session.rollback()
        print(f"Handle audio message error: {str(e)}")
        raise e

@jwt_required()
def add_message():
    """Add message to chat (API endpoint version)"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        chat_id = data.get('chatId')
        content = data.get('content')
        is_audio = data.get('isAudio', False)
        
        # Handle audio message
        if is_audio:
            if not chat_id or 'audioBase64' not in data:
                return jsonify({'message': 'Chat ID and audio data are required'}), 400
            
            # Verify the chat belongs to the user
            chat = Chat.query.filter_by(id=chat_id, user_id=user_id).first()
            
            if not chat:
                return jsonify({'message': 'Chat not found'}), 404
            
            # Process the audio message
            result = handle_audio_message({
                'chat_id': chat_id,
                'user_id': user_id,
                'audio_base64': data.get('audioBase64'),
                'audio_format': data.get('audioFormat', 'wav'),
                'language': data.get('language'),
                'tts_enabled': data.get('ttsEnabled', True),
                'voice_id': data.get('voiceId', '21m00Tcm4TlvDq8ikWAM')
            })
            
            return jsonify(result), 201
        
        # Handle text message
        if not chat_id or not content:
            return jsonify({'message': 'Chat ID and content are required'}), 400
        
        # Verify the chat belongs to the user
        chat = Chat.query.filter_by(id=chat_id, user_id=user_id).first()
        
        if not chat:
            return jsonify({'message': 'Chat not found'}), 404
        
        # Process the message using the handleMessage function
        result = handle_message({
            'chatId': chat_id,
            'content': content,
            'userId': user_id
        })
        
        return jsonify(result), 201
    except Exception as e:
        print(f"Add message error: {str(e)}")
        return jsonify({'message': 'Server error'}), 500

@jwt_required()
def get_message_by_id(message_id):
    """Get a single message by ID"""
    try:
        user_id = get_jwt_identity()
        message = Message.query.get(message_id)
        
        if not message:
            return jsonify({'message': 'Message not found'}), 404
        
        # Verify the message belongs to a chat owned by the user
        chat = Chat.query.filter_by(id=message.chat_id, user_id=user_id).first()
        
        if not chat:
            return jsonify({'message': 'Not authorized to access this message'}), 403
        
        return jsonify(message.to_dict()), 200
    except Exception as e:
        print(f"Get message by ID error: {str(e)}")
        return jsonify({'message': 'Server error'}), 500

@jwt_required()
def delete_message(message_id):
    """Delete a message"""
    try:
        user_id = get_jwt_identity()
        message = Message.query.get(message_id)
        
        if not message:
            return jsonify({'message': 'Message not found'}), 404
        
        # Verify the message belongs to a chat owned by the user
        chat = Chat.query.filter_by(id=message.chat_id, user_id=user_id).first()
        
        if not chat:
            return jsonify({'message': 'Not authorized to delete this message'}), 403
        
        db.session.delete(message)
        db.session.commit()
        
        return jsonify({'message': 'Message deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Delete message error: {str(e)}")
        return jsonify({'message': 'Server error'}), 500
