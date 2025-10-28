from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from speech.speech_processor import SpeechProcessor
from nlp.text_summarization import summarize_text
from models.db import db
from models.chat import Chat
from models.message import Message
from datetime import datetime

# Initialize SpeechProcessor (consider lazy loading or global instance if needed)
speech_processor = SpeechProcessor()

@jwt_required()
def process_speech_command():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        base64_audio = data.get('audio_base64')
        audio_format = data.get('audio_format', 'wav')
        chat_id = data.get('chat_id')

        if not base64_audio:
            return jsonify({'message': 'No audio data provided'}), 400

        # Transcribe audio
        transcription_result = speech_processor.transcribe_audio_base64(base64_audio, audio_format)

        if 'error' in transcription_result:
            return jsonify({'message': f"Transcription error: {transcription_result.get('error')}"}), 500

        transcribed_text = transcription_result.get('transcription', '')
        recognized_command = transcription_result.get('recognized_command')

        # Store user's speech as a message in conversation history
        user_message = Message(
            chat_id=chat_id,
            sender='user',
            content=f"[Voice Input]: {transcribed_text}",
            sentiment='neutral' # Sentiment can be analyzed here if needed
        )
        db.session.add(user_message)
        db.session.commit()

        response_message_content = f"Understood: {transcribed_text}."
        action_triggered = False

        # Act on recognized command
        if recognized_command == "summarize_document":
            # Placeholder: In a real scenario, you'd need to know *what* to summarize.
            # This might involve asking the user for context or looking at recent chat history.
            response_message_content = "Please provide the document or context you'd like me to summarize."
            # For demonstration, let's assume we summarize the last text message if available
            last_text_message = Message.query.filter_by(chat_id=chat_id, sender='user')\
                                .order_by(Message.timestamp.desc()).first()
            if last_text_message and last_text_message.content.startswith("[Voice Input]") == False:
                summary = summarize_text(last_text_message.content)
                response_message_content = f"Here's a summary of your last message: {summary}"
                action_triggered = True
            
        elif recognized_command == "set_reminder":
            response_message_content = "I can set a reminder. What should I remind you about and when?"
            action_triggered = True
        elif recognized_command == "create_task":
            response_message_content = "Okay, what is the task you'd like to create?"
            action_triggered = True
        elif recognized_command == "show_schedule":
            response_message_content = "I can show your schedule. Please connect your calendar first."
            action_triggered = True

        # Store AI's response
        ai_response_message = Message(
            chat_id=chat_id,
            sender='assistant',
            content=response_message_content,
            sentiment='neutral' # Sentiment can be analyzed here
        )
        db.session.add(ai_response_message)
        db.session.commit()

        # Update chat's last message and updated_at
        chat = Chat.query.get(chat_id)
        if chat:
            chat.last_message = ai_response_message.content
            chat.updated_at = datetime.utcnow()
            db.session.commit()

        return jsonify({
            'transcription': transcribed_text,
            'recognized_command': recognized_command,
            'ai_response': response_message_content,
            'action_triggered': action_triggered
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Process speech command error: {str(e)}")
        return jsonify({'message': 'Server error processing speech command'}), 500
