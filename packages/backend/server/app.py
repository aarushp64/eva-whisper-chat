from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from dotenv import load_dotenv
import os
import sys
import logging
import requests
from datetime import timedelta

# Load environment variables
load_dotenv()

# Ensure package root is on sys.path so imports like 'server.*' work when
# running `app.py` directly (start scripts may execute the file as a script).
_pkg_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _pkg_root not in sys.path:
    sys.path.insert(0, _pkg_root)

# Import routes (now that sys.path is configured)
from routes.auth_routes import auth_bp
from routes.chat_routes import chat_bp
from routes.user_routes import user_bp
from routes.file_routes import file_bp
from routes.speech_routes import speech_bp
from routes.group_routes import group_bp

# Import database
from models.db import db
from models.user import User
from models.chat import Chat
from models.message import Message
from models.user_preference import UserPreference
from models.group import Group
from models.group_member import GroupMember

# Import advanced features
from config.advanced_features import (
    is_feature_enabled, 
    get_module_config,
    MEMORY_CONFIG,
    NLP_CONFIG,
    SPEECH_CONFIG,
    ML_CONFIG,
    RAG_CONFIG,
    RESPONSE_CONFIG,
    DATABASE_CONFIG,
    DATA_ANALYTICS_CONFIG,
    USER_PERSONALIZATION_CONFIG
)

# Import advanced modules
from server.memory.memory_manager import MemoryManager
from server.nlp.entity_recognition_advanced import AdvancedEntityRecognition
from server.utils.advanced_response_generator import AdvancedResponseGenerator
from server.analytics.data_processor import DataProcessor
from server.analytics.ml_processor import MLProcessor
from server.analytics.user_personalization import UserPersonalizationEngine
from server.database.db_manager import DatabaseManager

 

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('eva.log')
    ]
)
logger = logging.getLogger('eva')

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'eva_secret_key_change_in_production')
# Configure the database URI from the environment variable, with a fallback to SQLite for local development
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI', 'sqlite:///eva.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt_secret_key_change_in_production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=30)

# Initialize extensions
CORS(app, resources={r"/*": {"origins": "*"}})
jwt = JWTManager(app)
socketio = SocketIO(app, cors_allowed_origins="*")
db.init_app(app)

# Initialize advanced components
db_manager = None
memory_manager = None
entity_recognition = None
response_generator = None
data_processor = None
ml_processor = None
user_personalization = None

# Initialize database manager if enabled
if is_feature_enabled('database'):
    logger.info("Initializing DatabaseManager")
    db_config = get_module_config('database')
    db_manager = DatabaseManager(
        config=db_config,
        default_type=db_config.get('default_type', 'sqlite')
    )

# Initialize memory manager if enabled
if is_feature_enabled('memory'):
    logger.info("Initializing MemoryManager")
    memory_config = get_module_config('memory')
    memory_manager = MemoryManager(
        config=memory_config,
        db_manager=db_manager
    )

# Initialize advanced entity recognition if enabled
if is_feature_enabled('entity_recognition'):
    logger.info("Initializing AdvancedEntityRecognition")
    nlp_config = get_module_config('nlp')
    entity_recognition = AdvancedEntityRecognition(
        config=nlp_config.get('entity_recognition', {}),
        memory_manager=memory_manager
    )

# Initialize data processor if enabled
if is_feature_enabled('data_analytics'):
    logger.info("Initializing DataProcessor")
    analytics_config = get_module_config('data_analytics')
    data_processor = DataProcessor(
        config=analytics_config
    )

# Initialize ML processor if enabled
if is_feature_enabled('ml'):
    logger.info("Initializing MLProcessor")
    ml_config = get_module_config('ml')
    ml_processor = MLProcessor(
        config=ml_config,
        data_processor=data_processor
    )

# Initialize user personalization if enabled
if is_feature_enabled('user_personalization'):
    logger.info("Initializing UserPersonalizationEngine")
    personalization_config = get_module_config('user_personalization')
    user_personalization = UserPersonalizationEngine(
        config=personalization_config,
        memory_manager=memory_manager,
        ml_processor=ml_processor
    )

# Initialize advanced response generator if enabled
if is_feature_enabled('response_generator'):
    logger.info("Initializing AdvancedResponseGenerator")
    response_config = get_module_config('response')
    response_generator = AdvancedResponseGenerator(
        config=response_config,
        memory_manager=memory_manager,
        entity_recognition=entity_recognition,
        user_personalization=user_personalization
    )

    # Import agent factory lazily (used for socket handling and routes)
    try:
        from core.agent_factory import get_agent
    except Exception:
        # get_agent will be imported where needed; keep import-time safe
        get_agent = None

# Import agent routes
from routes.agent_routes import agent_bp

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(chat_bp, url_prefix='/api/chat')
app.register_blueprint(user_bp, url_prefix='/api/user')
app.register_blueprint(file_bp, url_prefix='/api/file')
app.register_blueprint(speech_bp, url_prefix='/api/speech')
app.register_blueprint(group_bp, url_prefix='/api/group')
app.register_blueprint(agent_bp, url_prefix='/api/agent')

# Create database tables immediately at import time in this dev environment.
def create_tables():
    """Ensure DB tables exist. Run once at startup using the app context."""
    try:
        with app.app_context():
            db.create_all()
    except Exception:
        # If something goes wrong here, don't crash import-time; app will
        # attempt to create tables later when requests are handled.
        pass

# Run table creation now (useful for dev runs where we start app as a script)
create_tables()

# Socket.io events
from controllers.message_controller import handle_message

@socketio.on('connect')
def handle_connect():
    print('Client connected:', request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected:', request.sid)

@socketio.on('send_message')
def handle_send_message(data):
    try:
        logger.info(f"Received message from client {request.sid}")
        
        # Use advanced response generator if available
        if response_generator and is_feature_enabled('response_generator'):
            logger.info("Using advanced response generator")
            
            # Process the message with advanced features
            user_id = data.get('user_id')
            chat_id = data.get('chat_id')
            content = data.get('content')
            
            # Extract entities if available
            entities = None
            if entity_recognition and is_feature_enabled('entity_recognition'):
                entities = entity_recognition.extract_entities(content)
                logger.info(f"Extracted entities: {entities}")
            
            # Get user personalization if available
            user_profile = None
            if user_personalization and is_feature_enabled('user_personalization'):
                user_profile = user_personalization.get_user_profile(user_id)
                logger.info(f"Retrieved user profile for user {user_id}")
            
            # Generate response with advanced features
            response_data = response_generator.generate_response(
                user_id=user_id,
                chat_id=chat_id,
                message_content=content,
                entities=entities,
                user_profile=user_profile
            )
            
            # Update user profile with new interaction data
            if user_personalization and is_feature_enabled('user_personalization'):
                user_personalization.update_profile_from_interaction(
                    user_id=user_id,
                    message_content=content,
                    response_content=response_data.get('content'),
                    entities=entities
                )
                
            # Store in memory if available
            if memory_manager and is_feature_enabled('memory'):
                memory_manager.store_interaction(
                    user_id=user_id,
                    chat_id=chat_id,
                    message_content=content,
                    response_content=response_data.get('content'),
                    entities=entities
                )
                
            socketio.emit('receive_message', response_data, room=request.sid)
        else:
            # Try using Agent if available and enabled (non-blocking)
            used_agent = False
            try:
                # prefer get_agent if available; try import otherwise
                agent_getter = get_agent
                if agent_getter is None:
                    from core.agent_factory import get_agent as _get_agent
                    agent_getter = _get_agent

                # Only attempt agent if multi-agent feature is enabled
                if is_feature_enabled('multi_agent'):
                    agent = agent_getter()
                    if agent:
                        logger.info("Processing message through Agent (socket)")
                        # Prepare a simple Message-like conversation history if present
                        from core.llm.base_llm import Message
                        convo = []
                        # Optionally, you could pull recent conversation from memory_manager
                        result = agent.process_query(
                            query=content,
                            conversation_history=convo,
                            user_id=user_id
                        )
                        resp_payload = {
                            'content': result.get('response'),
                            'meta': {
                                'tool_calls': result.get('tool_calls', []),
                                'iterations': result.get('iterations', 1),
                                'model': result.get('model')
                            }
                        }

                        # Store memory if available
                        if memory_manager and is_feature_enabled('memory'):
                            memory_manager.store_interaction(
                                user_id=user_id,
                                chat_id=chat_id,
                                message_content=content,
                                response_content=resp_payload.get('content')
                            )

                        socketio.emit('receive_message', resp_payload, room=request.sid)
                        used_agent = True
            except Exception as e:
                logger.error(f"Agent processing failed in socket flow: {e}", exc_info=True)

            if not used_agent:
                # Fall back to original handler
                logger.info("Using original message handler")
                response = handle_message(data)
                socketio.emit('receive_message', response, room=request.sid)
            
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        socketio.emit('error', {'message': 'Error processing your message'}, room=request.sid)

# @socketio.on('send_audio')
# def handle_send_audio(data):
#     try:
#         logger.info(f"Received audio from client {request.sid}")
        
#         # Use advanced speech processing if enabled
#         if is_feature_enabled('speech_to_text'):
#             logger.info("Using advanced speech processing")
#             from speech.speech_processor import SpeechProcessor
            
#             # Get speech config
#             speech_config = get_module_config('speech')
#             stt_config = speech_config.get('speech_to_text', {})
            
#             # Initialize speech processor with advanced config
#             speech_processor = SpeechProcessor(
#                 whisper_model=stt_config.get('whisper_model', 'base'),
#                 elevenlabs_api_key=os.environ.get('ELEVENLABS_API_KEY'),
#                 config=speech_config
#             )
            
#             # Process audio
#             if 'audio_base64' not in data:
#                 socketio.emit('error', {'message': 'Missing audio data'}, room=request.sid)
#                 return
                
#             # Transcribe audio with advanced options
#             transcription = speech_processor.transcribe_audio_base64(
#                 data['audio_base64'],
#                 data.get('audio_format', 'wav'),
#                 data.get('language'),
#                 enhance_audio=stt_config.get('audio_enhancement', False),
#                 noise_reduction=stt_config.get('noise_reduction', False),
#                 diarization=stt_config.get('speaker_diarization', False)
#             )
            
#             if 'error' in transcription:
#                 logger.error(f"Transcription error: {transcription['error']}")
#                 socketio.emit('error', {'message': transcription['error']}, room=request.sid)
#                 return
            
#             logger.info(f"Transcription successful: {transcription['text'][:50]}...")
                
#             # Create message data with transcription
#             message_data = {
#                 'chat_id': data.get('chat_id'),
#                 'content': transcription['text'],
#                 'user_id': data.get('user_id'),
#                 'is_audio': True,
#                 'audio_metadata': {
#                     'duration': transcription.get('duration', data.get('duration')),
#                     'language': transcription.get('detected_language', transcription.get('language')),
#                     'confidence': transcription.get('confidence'),
#                     'model': stt_config.get('whisper_model', 'base')
#                 }
#             }
            
#             # Handle the transcribed message
#             response = handle_message(message_data)
            
#             # If TTS is enabled, generate speech response
#             if data.get('tts_enabled', False) and os.environ.get('ELEVENLABS_API_KEY'):
#                 try:
#                     speech_response = speech_processor.text_to_speech(
#                         response['content'],
#                         data.get('voice_id', '21m00Tcm4TlvDq8ikWAM')
#                     )
                    
#                     if 'error' not in speech_response:
#                         response['audio_response'] = speech_response['audio_base64']
#                         response['audio_format'] = speech_response['format']
#                 except Exception as e:
#                     logger.error(f"Error generating speech response: {str(e)}", exc_info=True)
            
#             # Use advanced response generator if available
#             if response_generator and is_feature_enabled('response_generator'):
#                 # Extract entities if available
#                 entities = None
#                 if entity_recognition and is_feature_enabled('entity_recognition'):
#                     entities = entity_recognition.extract_entities(transcription['text'])
#                     logger.info(f"Extracted entities from audio: {entities}")
                
#                 # Get user personalization if available
#                 user_profile = None
#                 if user_personalization and is_feature_enabled('user_personalization'):
#                     user_profile = user_personalization.get_user_profile(data.get('user_id'))
                
#                 # Generate response with advanced features
#                 response_data = response_generator.generate_response(
#                     user_id=data.get('user_id'),
#                     chat_id=data.get('chat_id'),
#                     message_content=transcription['text'],
#                     entities=entities,
#                     user_profile=user_profile,
#                     is_audio_input=True,
#                     audio_metadata=message_data.get('audio_metadata')
#                 )
                
#                 # Store in memory if available
#                 if memory_manager and is_feature_enabled('memory'):
#                     memory_manager.store_interaction(
#                         user_id=data.get('user_id'),
#                         chat_id=data.get('chat_id'),
#                         message_content=transcription['text'],
#                         response_content=response_data.get('content'),
#                         entities=entities,
#                         is_audio=True
#                     )
                
#                 socketio.emit('receive_message', response_data, room=request.sid)
#             else:
#                 # Fall back to original handler
#                 logger.info("Using original message handler for audio")
#                 response = handle_message(message_data)
#                 socketio.emit('receive_message', response, room=request.sid)
#         else: # This else is for the outer if (is_feature_enabled('speech_to_text'))
#             # Fall back to original speech processor if advanced features not enabled
#             logger.info("Using original speech processor")
#             from speech.speech_processor import SpeechProcessor
                
#             # Initialize speech processor
#             speech_processor = SpeechProcessor(
#                 whisper_model=os.environ.get('WHISPER_MODEL', 'base'),
#                 elevenlabs_api_key=os.environ.get('ELEVENLABS_API_KEY')
#             )
                
#             # Process audio
#             if 'audio_base64' not in data:
#                 socketio.emit('error', {'message': 'Missing audio data'}, room=request.sid)
#                 return
                    
#             # Transcribe audio
#             transcription = speech_processor.transcribe_audio_base64(
#                 data['audio_base64'],
#                 data.get('audio_format', 'wav'),
#                 data.get('language')
#             )
                
#             if 'error' in transcription:
#                 socketio.emit('error', {'message': transcription['error']}, room=request.sid)
#                 return
                    
#             # Create message data with transcription
#             message_data = {
#                 'chat_id': data.get('chat_id'),
#                 'content': transcription['text'],
#                 'user_id': data.get('user_id'),
#                 'is_audio': True,
#                 'audio_metadata': {
#                     'language': transcription.get('language'),
#                     'duration': data.get('duration')
#                 }
#             }
                
#             # Handle the transcribed message
#             response = handle_message(message_data)
#             socketio.emit('receive_message', response, room=request.sid)
#     except Exception as e:
#         logger.error(f"Error processing audio: {str(e)}", exc_info=True)
#         socketio.emit('error', {'message': 'Error processing your audio'}, room=request.sid)

# Default route
@app.route('/')
def index():
    return jsonify({'message': 'EVA Assistant API is running'})


@app.route('/api/health')
def health_check():
    """Health check endpoint for basic service availability.

    Returns JSON with service status and a simple check for the configured Ollama host.
    """
    status = {
        'service': 'eva-backend',
        'status': 'ok'
    }

    # Check Ollama host if configured
    ollama_host = os.environ.get('OLLAMA_HOST') or os.environ.get('LLM_HOST')
    if ollama_host:
        try:
            # simple GET to the root of the host with a short timeout
            r = requests.get(ollama_host, timeout=2)
            status['ollama'] = {'reachable': r.status_code == 200, 'status_code': r.status_code}
        except Exception as e:
            status['ollama'] = {'reachable': False, 'error': str(e)}
    else:
        status['ollama'] = {'reachable': False, 'error': 'OLLAMA_HOST not configured'}

    return jsonify(status)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
