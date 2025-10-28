import os
import random
import json
import importlib
import sys
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# Add server directory to path to allow imports from other modules
server_dir = Path(__file__).resolve().parent.parent
if str(server_dir) not in sys.path:
    sys.path.append(str(server_dir))

# Import utilities dynamically to avoid circular imports
from nlp.sentiment_analysis import get_emotional_intensity, analyze_sentiment_and_emotion
from nlp.intent_recognition import recognize_intent
from nlp.entity_recognition import extract_entities

# Load environment variables
load_dotenv()

# Fallback responses if LLM APIs are not available
FALLBACK_RESPONSES = {
    'positive': [
        "I'm glad to hear that! Tell me more about it.",
        "That sounds wonderful! I'm happy for you.",
        "That's great news! How does that make you feel?",
        "I'm really pleased to hear that. What's next for you?"
    ],
    'negative': [
        "I'm sorry to hear that. Would you like to talk more about it?",
        "That sounds challenging. How are you coping?",
        "I understand that must be difficult. I'm here to listen.",
        "I'm here for you. Would it help to discuss this further?"
    ],
    'neutral': [
        "I see. Could you tell me more about that?",
        "That's interesting. What are your thoughts on this?",
        "I'd like to understand better. Could you elaborate?",
        "Thanks for sharing. How do you feel about this?"
    ]
}

# Available LLM providers
LLM_PROVIDERS = ['openai', 'anthropic', 'google', 'cohere', 'local']

# Function to dynamically import LLM clients
def import_llm_client(provider):
    """
    Dynamically import LLM client based on provider
    """
    try:
        if provider == 'openai':
            import openai
            return openai
        elif provider == 'anthropic':
            import anthropic
            return anthropic
        elif provider == 'google':
            import google.generativeai as genai
            return genai
        elif provider == 'cohere':
            import cohere
            return cohere
        elif provider == 'local':
            # For local models like llama.cpp
            return None
        else:
            return None
    except ImportError:
        return None

# Initialize LLM clients
llm_clients = {}
for provider in LLM_PROVIDERS:
    llm_clients[provider] = import_llm_client(provider)

def generate_response(user_message, user_preference=None, sentiment=None, context=None, memory=None):
    """
    Generate an empathetic response based on user message, preferences, and context
    
    Args:
        user_message (str): The user's message
        user_preference (object): User preference object with communication style
        sentiment (str): Pre-analyzed sentiment (positive, negative, neutral)
        context (dict): Additional context for response generation
        memory (object): Conversation memory object
        
    Returns:
        dict: Response information including text and metadata
    """
    # Start timing for performance metrics
    start_time = datetime.now()
    
    # Process and analyze the message if not already done
    message_analysis = analyze_message(user_message, sentiment)
    sentiment = message_analysis['sentiment']
    
    # Determine which LLM provider to use
    provider = determine_llm_provider(user_preference, message_analysis)
    
    # Generate response using the selected provider
    try:
        if provider and llm_clients[provider]:
            response = generate_llm_response(user_message, user_preference, message_analysis, context, memory, provider)
        else:
            # Fallback to template responses
            response = generate_template_response(user_message, user_preference, sentiment)
            
        # Calculate response time
        response_time = (datetime.now() - start_time).total_seconds()
        
        # Format the response
        return format_response(response, message_analysis, response_time, provider)
    except Exception as e:
        print(f"Error generating response: {str(e)}")
        # Fallback to simple responses if any error occurs
        simple_response = random.choice(FALLBACK_RESPONSES[sentiment])
        return format_response(simple_response, message_analysis, 0, 'fallback')

def analyze_message(user_message, sentiment=None):
    """
    Analyze the user message for intent, entities, and sentiment
    """
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
    
    # Recognize intent
    intent = recognize_intent(user_message, method="ensemble")
    
    # Extract entities
    entities = extract_entities(user_message, methods=["spacy", "regex"])
    
    # Get emotional intensity
    emotional_intensity = get_emotional_intensity(user_message)
    
    return {
        'text': user_message,
        'sentiment': sentiment,
        'emotion': emotion,
        'sentiment_analysis': sentiment_analysis,
        'intent': intent,
        'entities': entities,
        'emotional_intensity': emotional_intensity,
        'timestamp': datetime.now().isoformat()
    }

def determine_llm_provider(user_preference, message_analysis):
    """
    Determine which LLM provider to use based on user preferences and message analysis
    """
    # Check for API keys
    available_providers = []
    for provider in LLM_PROVIDERS:
        if provider == 'openai' and (os.environ.get('OPENAI_API_KEY') or os.environ.get('OPENAI_API_KEY') != 'your_openai_api_key'):
            available_providers.append(provider)
        elif provider == 'anthropic' and os.environ.get('ANTHROPIC_API_KEY'):
            available_providers.append(provider)
        elif provider == 'google' and os.environ.get('GOOGLE_API_KEY'):
            available_providers.append(provider)
        elif provider == 'cohere' and os.environ.get('COHERE_API_KEY'):
            available_providers.append(provider)
        elif provider == 'local' and os.environ.get('LOCAL_LLM_ENDPOINT'):
            available_providers.append(provider)
    
    # If no providers are available, return None
    if not available_providers:
        return None
    
    # Check user preferences if available
    if user_preference and hasattr(user_preference, 'llm_provider') and user_preference.llm_provider in available_providers:
        return user_preference.llm_provider
    
    # Default to the first available provider
    return available_providers[0]

def generate_llm_response(user_message, user_preference, message_analysis, context, memory, provider):
    """
    Generate response using the specified LLM provider
    """
    # Get communication style from user preferences
    style = user_preference.communication_style if user_preference and hasattr(user_preference, 'communication_style') else 'empathetic'
    
    # Create system prompt based on communication style and analysis
    system_prompt = create_system_prompt(style, message_analysis, context, memory)
    
    # Get conversation history if available
    conversation_history = get_conversation_history(memory)
    
    # Generate response based on provider
    if provider == 'openai':
        return generate_openai_response(user_message, system_prompt, conversation_history, message_analysis)
    elif provider == 'anthropic':
        return generate_anthropic_response(user_message, system_prompt, conversation_history, message_analysis)
    elif provider == 'google':
        return generate_google_response(user_message, system_prompt, conversation_history, message_analysis)
    elif provider == 'cohere':
        return generate_cohere_response(user_message, system_prompt, conversation_history, message_analysis)
    elif provider == 'local':
        return generate_local_response(user_message, system_prompt, conversation_history, message_analysis)
    else:
        # Fallback to template responses
        return generate_template_response(user_message, user_preference, message_analysis['sentiment'])

def generate_openai_response(user_message, system_prompt, conversation_history, message_analysis):
    """
    Generate response using OpenAI API
    """
    openai = llm_clients['openai']
    if not openai:
        return generate_template_response(user_message, None, message_analysis['sentiment'])
    
    # Create messages for API call
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    # Add conversation history if available
    if conversation_history:
        messages.extend(conversation_history)
    
    # Add the current user message
    messages.append({"role": "user", "content": user_message})
    
    # Adjust temperature based on emotional intensity
    temperature = 0.7 + (message_analysis['emotional_intensity'] * 0.3)
    
    # Call OpenAI API
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=temperature,
            max_tokens=250,
            top_p=1,
            frequency_penalty=0.2,
            presence_penalty=0.6
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API error: {str(e)}")
        return generate_template_response(user_message, None, message_analysis['sentiment'])

def generate_anthropic_response(user_message, system_prompt, conversation_history, message_analysis):
    """
    Generate response using Anthropic API
    """
    anthropic = llm_clients['anthropic']
    if not anthropic:
        return generate_template_response(user_message, None, message_analysis['sentiment'])
    
    try:
        client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
        
        # Format conversation history for Anthropic
        formatted_history = ""
        if conversation_history:
            for msg in conversation_history:
                role = "Human" if msg["role"] == "user" else "Assistant"
                formatted_history += f"\n\n{role}: {msg['content']}"
        
        # Create the prompt
        prompt = f"{system_prompt}\n\n{formatted_history}\n\nHuman: {user_message}\n\nAssistant:"
        
        # Call Anthropic API
        response = client.completions.create(
            model="claude-2",
            prompt=prompt,
            max_tokens_to_sample=250,
            temperature=0.7 + (message_analysis['emotional_intensity'] * 0.3)
        )
        
        return response.completion
    except Exception as e:
        print(f"Anthropic API error: {str(e)}")
        return generate_template_response(user_message, None, message_analysis['sentiment'])

def generate_google_response(user_message, system_prompt, conversation_history, message_analysis):
    """
    Generate response using Google Generative AI
    """
    genai = llm_clients['google']
    if not genai:
        return generate_template_response(user_message, None, message_analysis['sentiment'])
    
    try:
        genai.configure(api_key=os.environ.get('GOOGLE_API_KEY'))
        
        # Format conversation for Google
        messages = []
        if conversation_history:
            for msg in conversation_history:
                role = "user" if msg["role"] == "user" else "model"
                messages.append({"role": role, "parts": [{"text": msg["content"]}]})
        
        # Add system prompt and current message
        messages = [
            {"role": "model", "parts": [{"text": system_prompt}]},
            *messages,
            {"role": "user", "parts": [{"text": user_message}]}
        ]
        
        # Call Google API
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(messages)
        
        return response.text
    except Exception as e:
        print(f"Google API error: {str(e)}")
        return generate_template_response(user_message, None, message_analysis['sentiment'])

def generate_cohere_response(user_message, system_prompt, conversation_history, message_analysis):
    """
    Generate response using Cohere API
    """
    cohere_module = llm_clients['cohere']
    if not cohere_module:
        return generate_template_response(user_message, None, message_analysis['sentiment'])
    
    try:
        client = cohere_module.Client(os.environ.get('COHERE_API_KEY'))
        
        # Format conversation for Cohere
        chat_history = []
        if conversation_history:
            for msg in conversation_history:
                role = "USER" if msg["role"] == "user" else "CHATBOT"
                chat_history.append({"role": role, "message": msg["content"]})
        
        # Call Cohere API
        response = client.chat(
            message=user_message,
            chat_history=chat_history,
            preamble=system_prompt,
            temperature=0.7 + (message_analysis['emotional_intensity'] * 0.3),
            max_tokens=250
        )
        
        return response.text
    except Exception as e:
        print(f"Cohere API error: {str(e)}")
        return generate_template_response(user_message, None, message_analysis['sentiment'])

def generate_local_response(user_message, system_prompt, conversation_history, message_analysis):
    """
    Generate response using local LLM endpoint
    """
    try:
        import requests
        
        # Format conversation for local LLM
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add conversation history if available
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add the current user message
        messages.append({"role": "user", "content": user_message})
        
        # Call local LLM API
        response = requests.post(
            os.environ.get('LOCAL_LLM_ENDPOINT'),
            json={
                "messages": messages,
                "temperature": 0.7 + (message_analysis['emotional_intensity'] * 0.3),
                "max_tokens": 250
            }
        )
        
        if response.status_code == 200:
            return response.json().get('response', '')
        else:
            print(f"Local LLM error: {response.status_code} - {response.text}")
            return generate_template_response(user_message, None, message_analysis['sentiment'])
    except Exception as e:
        print(f"Local LLM error: {str(e)}")
        return generate_template_response(user_message, None, message_analysis['sentiment'])

def generate_template_response(user_message, user_preference, sentiment):
    """
    Generate response using templates when LLM APIs are not available
    """
    # Get communication style
    style = user_preference.communication_style if user_preference and hasattr(user_preference, 'communication_style') else 'empathetic'
    
    # Select appropriate response template based on sentiment and style
    if style == 'empathetic':
        responses = FALLBACK_RESPONSES[sentiment]
    elif style == 'concise':
        # Shorter, more direct responses
        responses = [r.split('.')[0] + '.' for r in FALLBACK_RESPONSES[sentiment]]
    elif style == 'humorous':
        # Add a touch of humor
        responses = FALLBACK_RESPONSES[sentiment] + [
            "Well, that's one way to look at it! What's your take?",
            "Life's full of surprises, isn't it? Tell me more.",
            "That's quite something! What happened next?"
        ]
    else:
        # Default to standard responses
        responses = FALLBACK_RESPONSES[sentiment]
    
    return random.choice(responses)

def create_system_prompt(style, message_analysis, context=None, memory=None):
    """
    Create a system prompt for LLM based on communication style, message analysis, and context
    """
    base_prompt = "You are EVA, an empathetic, intelligent virtual assistant designed to communicate like a thoughtful and emotionally aware human being. You listen deeply, respond naturally, and adapt your tone based on the user's mood and context."
    
    style_prompts = {
        'casual': "Speak in a casual, friendly manner. Use conversational language and be approachable. Keep your tone light and informal.",
        'formal': "Maintain a professional and respectful tone. Use proper grammar and avoid colloquialisms. Be polite and structured in your responses.",
        'empathetic': "Focus on emotional understanding and support. Acknowledge feelings and show compassion. Validate the user's experiences and emotions.",
        'concise': "Be brief and to the point while remaining helpful. Avoid unnecessary elaboration. Provide clear, direct answers.",
        'humorous': "Incorporate appropriate humor and lightness when suitable, while remaining supportive. Use wit and playfulness in your responses.",
        'detailed': "Provide comprehensive and thorough responses. Include relevant details and explanations. Be informative and educational."
    }
    
    # Add sentiment and emotion guidance
    sentiment = message_analysis['sentiment']
    emotion = message_analysis['emotion']
    
    sentiment_guidance = {
        'positive': f"The user seems to be expressing positive emotions (detected: {emotion}). Match their energy while remaining authentic.",
        'negative': f"The user seems to be expressing negative emotions (detected: {emotion}). Be especially supportive and understanding.",
        'neutral': f"The user's tone is neutral. Respond thoughtfully and gauge their needs."
    }
    
    # Add intent guidance
    intent_type = message_analysis['intent'].get('intent', 'statement')
    intent_guidance = {
        'greeting': "The user is greeting you. Respond with a warm welcome.",
        'question': "The user is asking a question. Provide a helpful and informative answer.",
        'request': "The user is making a request. Be helpful and accommodating.",
        'command': "The user is giving a command. Acknowledge and respond appropriately.",
        'opinion': "The user is expressing an opinion. Acknowledge their perspective.",
        'statement': "The user is making a statement. Respond thoughtfully."
    }
    
    # Add memory context if available
    memory_context = ""
    if memory and hasattr(memory, 'get_relevant_context'):
        try:
            relevant_context = memory.get_relevant_context(message_analysis['text'])
            if relevant_context:
                memory_context = "\nRelevant conversation history: "
                for msg in relevant_context:
                    sender = "User" if msg.get("sender") == "user" else "You"
                    memory_context += f"\n- {sender}: {msg.get('content', '')}"
        except Exception as e:
            print(f"Error getting memory context: {str(e)}")
    
    # Add user preferences if available
    preference_context = ""
    if context and 'user_preferences' in context:
        preference_context = "\nUser preferences: " + json.dumps(context['user_preferences'])
    
    # Combine all prompts
    full_prompt = f"{base_prompt}\n\n{style_prompts.get(style, style_prompts['empathetic'])}\n\n{sentiment_guidance.get(sentiment, sentiment_guidance['neutral'])}\n\n{intent_guidance.get(intent_type, intent_guidance['statement'])}\n\nKeep your response concise, natural, and human-like. Avoid robotic phrasing.{memory_context}{preference_context}"
    
    return full_prompt

def get_conversation_history(memory, max_messages=5):
    """
    Get conversation history from memory for context
    """
    if not memory or not hasattr(memory, 'get_recent_messages'):
        return []
    
    try:
        recent_messages = memory.get_recent_messages(max_messages)
        
        # Format for LLM context
        formatted_messages = []
        for msg in recent_messages:
            role = "user" if msg.get("sender") == "user" else "assistant"
            formatted_messages.append({
                "role": role,
                "content": msg.get("content", "")
            })
        
        return formatted_messages
    except Exception as e:
        print(f"Error getting conversation history: {str(e)}")
        return []

def format_response(response_text, message_analysis, response_time, provider):
    """
    Format the final response with metadata
    """
    return {
        "text": response_text,
        "metadata": {
            "sentiment": message_analysis['sentiment'],
            "emotion": message_analysis['emotion'],
            "intent": message_analysis['intent'].get('intent', 'statement'),
            "entities": [], # Entities disabled for now
            "provider": provider,
            "response_time": response_time,
            "timestamp": datetime.now().isoformat()
        }
    }
