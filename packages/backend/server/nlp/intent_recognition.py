import spacy
# from transformers import pipeline
# from rasa.nlu.model import Interpreter
import os
import json
import re
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Union
from collections import Counter

# Import advanced features configuration
sys_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if sys_path not in os.sys.path:
    os.sys.path.append(sys_path)

from config.advanced_features import NLP_CONFIG, is_feature_enabled

# Get intent recognition config
intent_config = NLP_CONFIG.get("intent_recognition", {})
CONTEXT_AWARE = intent_config.get("context_aware", True)
MULTI_INTENT = intent_config.get("multi_intent", True)
CONFIDENCE_THRESHOLD = intent_config.get("confidence_threshold", 0.65)

# Load SpaCy model
try:
    nlp = spacy.load("en_core_web_md")
except OSError:
    # Download if not available
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_md"])
    nlp = spacy.load("en_core_web_md")

# Initialize HuggingFace pipeline for intent classification
intent_classifier = None

# Initialize RASA model (will be loaded on demand)
rasa_interpreter = None

# Intent categories with examples and patterns
INTENT_CATEGORIES = {
    "greeting": {
        "examples": ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"],
        "patterns": [r"^(?:hi|hello|hey)\b", r"^good (?:morning|afternoon|evening|day)"],
    },
    "farewell": {
        "examples": ["bye", "goodbye", "see you", "talk to you later", "farewell", "until next time"],
        "patterns": [r"^(?:bye|goodbye|farewell)\b", r"see you", r"talk (?:to|with) you later"],
    },
    "gratitude": {
        "examples": ["thank you", "thanks", "appreciate it", "grateful", "thank you so much"],
        "patterns": [r"thank(?:s| you)", r"appreciate", r"grateful"],
    },
    "question": {
        "examples": ["what", "when", "where", "who", "why", "how", "can you", "could you", "would you"],
        "patterns": [r"^(?:what|when|where|who|why|how)\b", r"\?", r"^(?:can|could|would) you"],
    },
    "request": {
        "examples": ["please", "can you", "could you", "would you", "I need", "I want", "help me"],
        "patterns": [r"please", r"(?:can|could|would) you", r"I (?:need|want|would like)", r"help me"],
    },
    "command": {
        "examples": ["find", "search", "look up", "tell me", "show", "display", "calculate", "compute"],
        "patterns": [r"^(?:find|search|look up|tell|show|display|calculate|compute)\b"],
    },
    "affirmation": {
        "examples": ["yes", "yeah", "yep", "sure", "absolutely", "definitely", "correct", "right"],
        "patterns": [r"^(?:yes|yeah|yep|sure|absolutely|definitely|correct|right)\b"],
    },
    "negation": {
        "examples": ["no", "nope", "not", "don't", "can't", "won't", "incorrect", "wrong"],
        "patterns": [r"^(?:no|nope)\b", r"\b(?:not|don't|can't|won't|incorrect|wrong)\b"],
    },
    "opinion": {
        "examples": ["I think", "I believe", "in my opinion", "I feel", "from my perspective"],
        "patterns": [r"I (?:think|believe|feel)", r"(?:my|in my) (?:opinion|perspective|view)"],
    },
    "clarification": {
        "examples": ["what do you mean", "I don't understand", "can you explain", "I'm confused"],
        "patterns": [r"what do you mean", r"I don't understand", r"can you explain", r"I'm confused"],
    },
    "confirmation": {
        "examples": ["is that right", "did you mean", "are you sure", "to confirm", "to be clear"],
        "patterns": [r"is that (?:right|correct)", r"did you mean", r"are you sure", r"to (?:confirm|be clear)"],
    },
    "information": {
        "examples": ["I want to know", "tell me about", "information on", "details about", "facts about"],
        "patterns": [r"I want to know", r"tell me about", r"information on", r"details about", r"facts about"],
    },
    "preference": {
        "examples": ["I prefer", "I'd rather", "I like", "I love", "I hate", "I dislike", "I enjoy"],
        "patterns": [r"I (?:prefer|like|love|hate|dislike|enjoy)", r"I'd rather"],
    },
    "suggestion": {
        "examples": ["maybe", "perhaps", "what about", "how about", "we could", "you could"],
        "patterns": [r"^(?:maybe|perhaps)\b", r"what about", r"how about", r"(?:we|you) could"],
    },
    "complaint": {
        "examples": ["I'm not happy", "this isn't working", "I have a problem", "this is frustrating"],
        "patterns": [r"(?:not happy|isn't working|have a problem|frustrating|annoying)"],
    },
    "feedback": {
        "examples": ["I like how", "I don't like", "this is good", "this is bad", "this could be better"],
        "patterns": [r"I (?:like|don't like)", r"this is (?:good|bad|great|terrible)", r"could be better"],
    },
    "data_query": {
        "examples": ["analyze", "data", "statistics", "graph", "chart", "plot", "dataset", "correlation"],
        "patterns": [r"\b(?:analyze|data|statistics|graph|chart|plot|dataset|correlation)\b"],
    },
    "web_search": {
        "examples": ["search for", "find information", "look up", "search the web", "google", "research"],
        "patterns": [r"search (?:for|the web)", r"find information", r"look up", r"google", r"research"],
    },
    "system": {
        "examples": ["settings", "configure", "preferences", "setup", "system", "change settings"],
        "patterns": [r"\b(?:settings|configure|preferences|setup|system)\b", r"change (?:settings|configuration)"],
    },
    "summarize_document": {
        "examples": ["summarize this", "make a summary", "give me the gist"],
        "patterns": [r"summarize this", r"make a summary", r"give me the gist"],
    },
    "set_reminder": {
        "examples": ["set a reminder", "remind me", "create a reminder"],
        "patterns": [r"set a reminder", r"remind me", r"create a reminder"],
    },
    "create_task": {
        "examples": ["create a task", "add a task", "new task"],
        "patterns": [r"create a task", r"add a task", r"new task"],
    },
    "show_schedule": {
        "examples": ["show my schedule", "what's my schedule", "my appointments"],
        "patterns": [r"show my schedule", r"what's my schedule", r"my appointments"],
    },
}

# def initialize_huggingface_intent_classifier():
#     """Initialize the HuggingFace intent classifier"""
#     global intent_classifier
#     try:
#         intent_classifier = pipeline(
#             "text-classification", 
#             model="facebook/bart-large-mnli", 
#             return_all_scores=True
#         )
#     except Exception as e:
#         print(f"Error initializing HuggingFace intent classifier: {str(e)}")
#         # Fallback to simpler model if needed
#         try:
#             intent_classifier = pipeline(
#                 "text-classification", 
#                 model="distilbert-base-uncased-finetuned-sst-2-english",
#                 return_all_scores=True
#             )
#         except Exception as e:
#             print(f"Error initializing fallback intent classifier: {str(e)}")

# def initialize_rasa_interpreter():
#     """Initialize the RASA NLU interpreter"""
#     global rasa_interpreter
#     try:
#         # Check if RASA model exists
#         model_path = Path("models/nlu")
#         if not model_path.exists():
#             print("RASA model not found. Will use other intent recognition methods.")
#             return
        
#         # Get the latest model
#         models = list(model_path.glob("*"))
#         if not models:
#             print("No RASA models found in models/nlu directory")
#             return
            
#         latest_model = str(max(models, key=os.path.getctime))
#         rasa_interpreter = Interpreter.load(latest_model)
#     except Exception as e:
#         print(f"Error initializing RASA interpreter: {str(e)}")

def get_intent_spacy(text):
    """Extract intent using SpaCy's rule-based matching with enhanced patterns"""
    doc = nlp(text)
    text_lower = text.lower()
    
    # Check for question marks (high priority)
    if "?" in text:
        # Determine question type
        if any(w.lower_ in ["what", "when", "where", "who", "why", "how"] for w in doc):
            return "question"
        elif any(w.lower_ in ["can", "could", "would", "will", "should"] for w in doc[:2]):
            return "request" if "you" in text_lower else "question"
        else:
            return "question"
    
    # Check for command structure (imperative verbs at beginning)
    if len(doc) > 0 and doc[0].pos_ == "VERB":
        return "command"
    
    # Check for patterns in each intent category
    scores = {}
    for intent, data in INTENT_CATEGORIES.items():
        score = 0
        # Check for exact keyword matches
        for keyword in data["examples"]:
            if keyword in text_lower:
                score += 1
        
        # Check for regex pattern matches
        for pattern in data["patterns"]:
            if re.search(pattern, text_lower):
                score += 2  # Patterns are more specific, so higher score
        
        if score > 0:
            scores[intent] = score
    
    # Return the intent with the highest score, or default to "statement"
    if scores:
        return max(scores.items(), key=lambda x: x[1])[0]
    
    # Use SpaCy's semantic understanding for more nuanced detection
    if doc[0].lemma_ in ["be", "do", "have"] and len(doc) > 1 and doc[1].text.lower() in ["you", "i", "we", "they"]:
        return "question"
    
    # Check for statements that express opinions
    if any(token.lemma_ in ["think", "believe", "feel"] for token in doc) and any(token.text.lower() == "i" for token in doc):
        return "opinion"
    
    # Default to statement if no specific intent is found
    return "statement"

# def get_intent_huggingface(text, candidate_labels=None):
#     """Extract intent using HuggingFace transformers"""
#     global intent_classifier
    
#     if intent_classifier is None:
#         initialize_huggingface_intent_classifier()
#         if intent_classifier is None:
#             return None
    
#     if candidate_labels is None:
#         candidate_labels = [
#             "greeting", "farewell", "question", "request", "command",
#             "information", "opinion", "feedback", "gratitude", "complaint"
#         ]
    
#     try:
#         # Run zero-shot classification
#         result = intent_classifier(text, candidate_labels)
        
#         # Get the highest scoring intent
#         top_intent = max(result[0], key=lambda x: x['score'])
#         return {
#             "intent": top_intent['label'],
#             "confidence": top_intent['score'],
#             "all_intents": result[0]
#         }
#     except Exception as e:
#         print(f"Error in HuggingFace intent recognition: {str(e)}")
#         return None

# def get_intent_rasa(text):
#     """Extract intent using RASA NLU"""
#     global rasa_interpreter
    
#     if rasa_interpreter is None:
#         initialize_rasa_interpreter()
#         if rasa_interpreter is None:
#             return None
    
#     try:
#         result = rasa_interpreter.parse(text)
#         return {
#             "intent": result.get("intent", {}).get("name"),
#             "confidence": result.get("intent", {}).get("confidence"),
#             "entities": result.get("entities", [])
#         }
#     except Exception as e:
#         print(f"Error in RASA intent recognition: {str(e)}")
#         return None

def recognize_intent(text, method="ensemble", context=None):
    """
    Recognize user intent from text using specified method
    
    Args:
        text (str): User input text
        method (str): Method to use - "spacy", "huggingface", "rasa", or "ensemble"
        context (dict): Optional context information including:
            - previous_intents: List of previous intents in the conversation
            - conversation_history: List of previous messages
            - user_profile: User profile information
            - current_topic: Current conversation topic
        
    Returns:
        dict: Intent information including intent name and confidence
              If multi-intent detection is enabled, may return multiple intents
    """
    # Use context-aware intent recognition if enabled and context is provided
    if CONTEXT_AWARE and context:
        # Import here to avoid circular imports
        from nlp.intent_recognition_advanced import recognize_intent_with_context
        return recognize_intent_with_context(text, method)
    
    # Use multi-intent detection if enabled
    if MULTI_INTENT:
        # Import here to avoid circular imports
        from nlp.intent_recognition_advanced import detect_multiple_intents
        return detect_multiple_intents(text, method)
    
    # Standard single intent recognition
    # Always use spacy for now
    intent = get_intent_spacy(text)
    return {"intent": intent, "confidence": 0.7, "method": "spacy"}