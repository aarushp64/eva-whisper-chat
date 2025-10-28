"""
Advanced Response Generator

This module enhances the base response generator with:
1. Advanced memory integration
2. Contextual awareness
3. Personalization
4. Multi-modal response capabilities
5. Multiple LLM provider support
"""

import os
import random
import json
import importlib
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
import logging

# Add server directory to path to allow imports from other modules
server_dir = Path(__file__).resolve().parent.parent
if str(server_dir) not in sys.path:
    sys.path.append(str(server_dir))

# Import from base response generator
from utils.response_generator import (
    generate_response as base_generate_response,
    analyze_message,
    determine_llm_provider,
    generate_llm_response,
    generate_template_response,
    create_system_prompt,
    format_response,
    FALLBACK_RESPONSES,
    LLM_PROVIDERS
)

# Import NLP modules
from nlp.sentiment_analysis import analyze_sentiment_and_emotion
from nlp.intent_recognition import recognize_intent
from nlp.intent_recognition_advanced import recognize_intent_with_context, detect_multiple_intents
from nlp.entity_recognition import extract_entities
from nlp.entity_recognition_advanced import extract_entities_with_context, extract_hierarchical_entities

# Import memory system
from memory.memory_manager import get_memory_manager, MemoryManager

# Import advanced features configuration
from config.advanced_features import NLP_CONFIG, LLM_CONFIG, MEMORY_CONFIG, is_feature_enabled

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get memory manager
memory_manager = get_memory_manager()

def generate_response_with_memory(
    user_message: str,
    user_id: str,
    chat_id: Optional[str] = None,
    user_preference: Optional[Dict[str, Any]] = None,
    sentiment: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate an empathetic response with memory integration
    
    Args:
        user_message: The user's message
        user_id: User ID for memory retrieval
        chat_id: Chat ID for conversation context
        user_preference: User preference object with communication style
        sentiment: Pre-analyzed sentiment (positive, negative, neutral)
        context: Additional context for response generation
        
    Returns:
        Response information including text and metadata
    """
    # Start timing for performance metrics
    start_time = datetime.now()
    
    # Initialize context if not provided
    if context is None:
        context = {}
    
    # Get user profile from memory
    user_profile = memory_manager.get_user_profile(user_id)
    
    # Get conversation memory
    conversation_memory = memory_manager.get_conversation_memory(user_id, chat_id)
    
    # Get hierarchical memory
    hierarchical_memory = memory_manager.get_hierarchical_memory(user_id, chat_id)
    
    # Process and analyze the message with context
    message_analysis = analyze_message_with_context(
        user_message, 
        user_id, 
        chat_id,
        sentiment=sentiment, 
        conversation_memory=conversation_memory
    )
    
    # Update context with memory information
    memory_context = get_memory_context(user_id, user_message, message_analysis, chat_id)
    context.update(memory_context)
    
    # Add user profile to context
    context["user_profile"] = {
        "preferences": user_profile.profile_data["preferences"],
        "personal_info": user_profile.profile_data["personal_info"],
        "favorite_topics": user_profile.get_favorite_topics()
    }
    
    # Determine which LLM provider to use
    provider = determine_llm_provider(user_preference, message_analysis)
    
    # Generate response using the selected provider
    try:
        if provider:
            response = generate_enhanced_llm_response(
                user_message, 
                user_preference, 
                message_analysis, 
                context, 
                conversation_memory, 
                provider
            )
        else:
            # Fallback to template responses
            response = generate_template_response(
                user_message, 
                user_preference, 
                message_analysis["sentiment"]
            )
        
        # Calculate response time
        response_time = (datetime.now() - start_time).total_seconds()
        
        # Format the response
        formatted_response = format_response(response, message_analysis, response_time, provider)
        
        # Store the response in memory
        store_interaction_in_memory(
            user_id, 
            user_message, 
            formatted_response["text"], 
            message_analysis, 
            chat_id
        )
        
        return formatted_response
    
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        # Fallback to simple responses if any error occurs
        simple_response = random.choice(FALLBACK_RESPONSES[message_analysis["sentiment"]])
        return format_response(simple_response, message_analysis, 0, 'fallback')

def analyze_message_with_context(
    user_message: str, 
    user_id: str, 
    chat_id: Optional[str] = None,
    sentiment: Optional[str] = None, 
    conversation_memory = None
) -> Dict[str, Any]:
    """
    Analyze the user message with context from memory
    
    Args:
        user_message: User's message text
        user_id: User ID for memory retrieval
        chat_id: Chat ID for conversation context
        sentiment: Pre-analyzed sentiment
        conversation_memory: Conversation memory object
        
    Returns:
        Analysis results including intent, entities, sentiment, etc.
    """
    # Get conversation history for context
    conversation_history = []
    if conversation_memory:
        conversation_history = conversation_memory.messages
    
    # Analyze sentiment if not provided
    if not sentiment:
        sentiment_analysis = analyze_sentiment_and_emotion(user_message)
        sentiment = sentiment_analysis['dominant_sentiment']
        emotion = sentiment_analysis['dominant_emotion']
    else:
        # Basic sentiment analysis for emotion
        emotion = 'neutral'
        if sentiment == 'positive':
            emotion = 'joy'
        elif sentiment == 'negative':
            emotion = 'sadness'
        sentiment_analysis = {
            'dominant_sentiment': sentiment,
            'dominant_emotion': emotion
        }
    
    # Create context for advanced NLP
    context = {
        "conversation_history": conversation_history,
        "user_id": user_id,
        "chat_id": chat_id
    }
    
    # Check if advanced intent recognition is enabled
    if is_feature_enabled("nlp.intent_recognition.contextual"):
        # Recognize intent with context
        intent = recognize_intent_with_context(user_message, context)
    else:
        # Use basic intent recognition
        intent = recognize_intent(user_message, method="ensemble")
    
    # Check if multi-intent detection is enabled
    if is_feature_enabled("nlp.intent_recognition.multi_intent"):
        # Detect multiple intents
        intents = detect_multiple_intents(user_message)
    else:
        intents = [intent]
    
    # Check if advanced entity recognition is enabled
    if is_feature_enabled("nlp.entity_recognition.contextual"):
        # Extract entities with context
        entities = extract_entities_with_context(user_message, context)
    else:
        # Use basic entity extraction
        entities = extract_entities(user_message, methods=["spacy", "regex"])
    
    # Check if hierarchical entity recognition is enabled
    if is_feature_enabled("nlp.entity_recognition.hierarchical"):
        # Extract hierarchical entities
        hierarchical_entities = extract_hierarchical_entities(user_message)
    else:
        hierarchical_entities = None
    
    return {
        'text': user_message,
        'sentiment': sentiment,
        'emotion': emotion,
        'sentiment_analysis': sentiment_analysis,
        'intent': intent,
        'intents': intents,
        'entities': entities,
        'hierarchical_entities': hierarchical_entities,
        'timestamp': datetime.now().isoformat()
    }

def get_memory_context(
    user_id: str, 
    user_message: str, 
    message_analysis: Dict[str, Any], 
    chat_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get relevant context from memory for response generation
    
    Args:
        user_id: User ID for memory retrieval
        user_message: User's message text
        message_analysis: Analysis of the user message
        chat_id: Chat ID for conversation context
        
    Returns:
        Memory context for response generation
    """
    # Get hierarchical memory
    hierarchical_memory = memory_manager.get_hierarchical_memory(user_id, chat_id)
    
    # Get relevant memories
    relevant_memories = hierarchical_memory.get_relevant_memories(user_message, k=5)
    
    # Get user profile
    user_profile = memory_manager.get_user_profile(user_id)
    
    # Extract entities for knowledge base search
    entities = message_analysis.get("entities", [])
    entity_texts = [entity["text"] for entity in entities]
    
    # Search knowledge bases for relevant information
    kb_results = []
    for entity_text in entity_texts:
        kb_results.extend(memory_manager.search_knowledge_base(entity_text))
    
    # Compile memory context
    memory_context = {
        "relevant_memories": relevant_memories,
        "user_profile": {
            "preferences": user_profile.profile_data["preferences"],
            "personal_info": user_profile.profile_data["personal_info"],
            "favorite_topics": user_profile.get_favorite_topics()
        },
        "knowledge_base_results": kb_results,
        "session_id": chat_id,
        "timestamp": datetime.now().isoformat()
    }
    
    return memory_context

def generate_enhanced_llm_response(
    user_message: str, 
    user_preference: Optional[Dict[str, Any]], 
    message_analysis: Dict[str, Any], 
    context: Dict[str, Any], 
    conversation_memory, 
    provider: str
) -> str:
    """
    Generate enhanced response using LLM with memory context
    
    Args:
        user_message: User's message text
        user_preference: User preferences
        message_analysis: Analysis of the user message
        context: Additional context including memory
        conversation_memory: Conversation memory object
        provider: LLM provider to use
        
    Returns:
        Generated response text
    """
    # Get communication style from user preferences
    style = user_preference.get("communication_style", "empathetic") if user_preference else "empathetic"
    
    # Create enhanced system prompt with memory context
    system_prompt = create_enhanced_system_prompt(style, message_analysis, context)
    
    # Get conversation history
    conversation_history = []
    if conversation_memory:
        conversation_history = conversation_memory.messages
    
    # Use the base LLM response generator with enhanced prompt
    return generate_llm_response(
        user_message, 
        user_preference, 
        message_analysis, 
        context, 
        conversation_memory, 
        provider, 
        system_prompt=system_prompt
    )

def create_enhanced_system_prompt(
    style: str, 
    message_analysis: Dict[str, Any], 
    context: Dict[str, Any]
) -> str:
    """
    Create an enhanced system prompt with memory integration
    
    Args:
        style: Communication style
        message_analysis: Analysis of the user message
        context: Additional context including memory
        
    Returns:
        Enhanced system prompt
    """
    # Base prompt from communication style
    base_prompt = f"You are EVA, an empathetic and helpful AI assistant. "
    
    # Add style-specific instructions
    if style == "empathetic":
        base_prompt += "Focus on understanding and validating the user's emotions. "
    elif style == "informative":
        base_prompt += "Focus on providing clear, accurate information. "
    elif style == "concise":
        base_prompt += "Be brief and to the point while remaining helpful. "
    elif style == "friendly":
        base_prompt += "Be warm, conversational, and approachable. "
    elif style == "professional":
        base_prompt += "Maintain a professional, respectful tone. "
    
    # Add user profile information if available
    if "user_profile" in context:
        user_profile = context["user_profile"]
        
        # Add personal information
        if user_profile.get("personal_info"):
            personal_info = user_profile["personal_info"]
            base_prompt += "The user has shared the following personal information: "
            
            for key, value in personal_info.items():
                if key and value:  # Only include non-empty values
                    base_prompt += f"{key}: {value}, "
            
            base_prompt = base_prompt.rstrip(", ") + ". "
        
        # Add preferences
        if user_profile.get("preferences"):
            preferences = user_profile["preferences"]
            base_prompt += "The user has the following preferences: "
            
            for key, value in preferences.items():
                if key and value:  # Only include non-empty values
                    base_prompt += f"{key}: {value}, "
            
            base_prompt = base_prompt.rstrip(", ") + ". "
        
        # Add favorite topics
        if user_profile.get("favorite_topics"):
            topics = user_profile["favorite_topics"]
            if topics:
                base_prompt += "The user frequently discusses: "
                topics_str = ", ".join([t["topic"] for t in topics[:3]])
                base_prompt += f"{topics_str}. "
    
    # Add relevant memories if available
    if "relevant_memories" in context and context["relevant_memories"]:
        memories = context["relevant_memories"]
        base_prompt += "Based on previous conversations, remember: "
        
        # Add up to 3 most important memories
        for i, memory in enumerate(memories[:3]):
            if "content" in memory:
                base_prompt += f"{memory['content']}. "
    
    # Add knowledge base information if available
    if "knowledge_base_results" in context and context["knowledge_base_results"]:
        kb_results = context["knowledge_base_results"]
        base_prompt += "You have access to the following information: "
        
        # Add up to 3 most relevant knowledge base results
        for i, result in enumerate(kb_results[:3]):
            if "entity" in result and "name" in result["entity"]:
                entity = result["entity"]
                base_prompt += f"{entity['name']}: {entity.get('description', '')}. "
    
    # Add message analysis
    intent = message_analysis.get("intent", "")
    emotion = message_analysis.get("emotion", "")
    
    base_prompt += f"The user's message appears to have the intent: {intent}. "
    base_prompt += f"The user seems to be feeling: {emotion}. "
    
    # Add response instructions
    base_prompt += "Respond in a way that acknowledges their intent and emotional state. "
    base_prompt += "Be conversational, helpful, and concise. "
    
    return base_prompt

def store_interaction_in_memory(
    user_id: str, 
    user_message: str, 
    assistant_response: str, 
    message_analysis: Dict[str, Any], 
    chat_id: Optional[str] = None
) -> None:
    """
    Store the interaction in memory for future reference
    
    Args:
        user_id: User ID
        user_message: User's message text
        assistant_response: Assistant's response text
        message_analysis: Analysis of the user message
        chat_id: Chat ID for conversation context
    """
    # Get memory manager
    memory_mgr = get_memory_manager()
    
    # Create user message object
    user_message_obj = {
        "sender": "user",
        "content": user_message,
        "timestamp": datetime.now().isoformat()
    }
    
    # Create assistant message object
    assistant_message_obj = {
        "sender": "assistant",
        "content": assistant_response,
        "timestamp": datetime.now().isoformat()
    }
    
    # Add messages to conversation memory
    memory_mgr.add_conversation_message(user_id, user_message_obj, chat_id)
    memory_mgr.add_conversation_message(user_id, assistant_message_obj, chat_id)
    
    # Add to hierarchical memory with metadata
    user_metadata = {
        "message_id": str(datetime.now().timestamp()),
        "chat_id": chat_id,
        "category": "conversation",
        "intent": message_analysis.get("intent", ""),
        "emotion": message_analysis.get("emotion", ""),
        "sentiment": message_analysis.get("sentiment", "")
    }
    
    assistant_metadata = {
        "message_id": str(datetime.now().timestamp() + 1),
        "chat_id": chat_id,
        "category": "conversation",
        "in_response_to": user_metadata["message_id"]
    }
    
    # Add to memory
    memory_mgr.add_memory(
        user_id=user_id,
        content=user_message,
        source="conversation:user",
        metadata=user_metadata,
        session_id=chat_id
    )
    
    memory_mgr.add_memory(
        user_id=user_id,
        content=assistant_response,
        source="conversation:assistant",
        metadata=assistant_metadata,
        session_id=chat_id
    )
    
    # Update user profile based on interaction
    user_profile = memory_mgr.get_user_profile(user_id)
    
    # Record message with topic
    intent = message_analysis.get("intent", "")
    user_profile.record_message(topic=intent)
    
    # Extract and store user preferences if detected
    entities = message_analysis.get("entities", [])
    for entity in entities:
        if entity.get("label") in ["PREFERENCE", "LIKE", "DISLIKE"]:
            preference_key = f"preference_{len(user_profile.profile_data['preferences']) + 1}"
            user_profile.update_preference(preference_key, entity["text"])
        
        # Extract and store personal information if detected
        if entity.get("label") in ["PERSON", "LOCATION", "ORGANIZATION", "DATE"]:
            # Only store if it seems to be related to the user
            if "my" in user_message.lower() or "i" in user_message.lower():
                info_key = f"personal_info_{len(user_profile.profile_data['personal_info']) + 1}"
                user_profile.update_personal_info(info_key, entity["text"])
    
    # Save memory periodically
    if datetime.now().second % 30 == 0:  # Save every 30 seconds
        memory_mgr.save_all()

def generate_multimodal_response(
    user_message: str,
    user_id: str,
    chat_id: Optional[str] = None,
    user_preference: Optional[Dict[str, Any]] = None,
    media_content: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate a multimodal response (text + other media types)
    
    Args:
        user_message: The user's message
        user_id: User ID for memory retrieval
        chat_id: Chat ID for conversation context
        user_preference: User preference object
        media_content: Additional media content from user (images, audio, etc.)
        context: Additional context for response generation
        
    Returns:
        Multimodal response with text and other media
    """
    # Generate text response
    text_response = generate_response_with_memory(
        user_message, 
        user_id, 
        chat_id, 
        user_preference, 
        None, 
        context
    )
    
    # Initialize multimodal response with text
    multimodal_response = {
        "text": text_response["text"],
        "metadata": text_response["metadata"],
        "media": []
    }
    
    # Check if multimodal features are enabled
    if not is_feature_enabled("response.multimodal"):
        return multimodal_response
    
    # Process based on detected intents
    intent = text_response["metadata"]["intent"]
    
    # Add media based on intent
    if "image" in intent or "visual" in intent or "show" in intent:
        # Add image response if appropriate
        multimodal_response["media"].append({
            "type": "image",
            "url": "placeholder_for_image_generation",  # Would be replaced with actual image generation
            "alt_text": "Generated image based on user request"
        })
    
    elif "chart" in intent or "graph" in intent or "data" in intent:
        # Add chart response if appropriate
        multimodal_response["media"].append({
            "type": "chart",
            "data": "placeholder_for_chart_data",  # Would be replaced with actual chart data
            "chart_type": "bar"  # Default chart type
        })
    
    # Return the multimodal response
    return multimodal_response


class AdvancedResponseGenerator:
    """Lightweight wrapper that provides the interface used by the rest of
    the application. It delegates to the functions in this module. This is a
    minimal implementation to allow the backend to run without the full
    production pipeline.
    """
    def __init__(self, config: Dict[str, Any] = None, memory_manager=None, entity_recognition=None, user_personalization=None):
        self.config = config or {}
        self.memory_manager = memory_manager or memory_manager
        self.entity_recognition = entity_recognition
        self.user_personalization = user_personalization

    def generate_response(self, user_id: str = None, chat_id: str = None, message_content: str = None, entities: Optional[List[Dict[str, Any]]] = None, user_profile: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        # Create a simple context including entities if provided
        context = kwargs.get('context', {})
        if entities:
            context['entities'] = entities

        formatted = generate_response_with_memory(
            user_message=message_content,
            user_id=user_id,
            chat_id=chat_id,
            user_preference=user_profile,
            sentiment=None,
            context=context
        )

        # Return a minimal payload similar to what the production generator would
        return {
            'content': formatted.get('text') if isinstance(formatted, dict) else formatted,
            'metadata': formatted.get('metadata') if isinstance(formatted, dict) else {}
        }
