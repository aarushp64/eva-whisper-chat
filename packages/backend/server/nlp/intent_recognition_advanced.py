"""
Advanced Intent Recognition Module

This module extends the basic intent recognition with:
1. Context-aware intent recognition
2. Multi-intent detection
3. Intent confidence scoring
4. Domain-specific intent models
"""

import os
import re
import json
import numpy as np
from typing import List, Dict, Any, Tuple, Optional, Union
from collections import Counter
from pathlib import Path

# Import from base intent recognition. Use getattr fallbacks so advanced
# module can operate even if some intent backends (HuggingFace/Rasa) are
# disabled or not installed.
import nlp.intent_recognition as _base_intent

get_intent_spacy = getattr(_base_intent, 'get_intent_spacy', lambda text: 'statement')
get_intent_huggingface = getattr(_base_intent, 'get_intent_huggingface', lambda text: {'intent': 'statement', 'confidence': 0.5})
get_intent_rasa = getattr(_base_intent, 'get_intent_rasa', lambda text: {'intent': 'statement', 'confidence': 0.5})
INTENT_CATEGORIES = getattr(_base_intent, 'INTENT_CATEGORIES', {})
nlp = getattr(_base_intent, 'nlp', None)

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

# Intent transition probabilities (for context-aware recognition)
# Higher values indicate more likely transitions between intents
INTENT_TRANSITIONS = {
    "greeting": {
        "question": 0.8,
        "information": 0.7,
        "request": 0.6,
        "statement": 0.5,
        "farewell": 0.1
    },
    "question": {
        "clarification": 0.8,
        "information": 0.7,
        "opinion": 0.6,
        "question": 0.5,
        "affirmation": 0.4,
        "negation": 0.4
    },
    "request": {
        "clarification": 0.7,
        "affirmation": 0.6,
        "negation": 0.6,
        "question": 0.5,
        "information": 0.4
    },
    "information": {
        "question": 0.7,
        "opinion": 0.6,
        "information": 0.5,
        "gratitude": 0.4
    },
    "opinion": {
        "question": 0.7,
        "opinion": 0.6,
        "information": 0.5,
        "agreement": 0.4,
        "disagreement": 0.4
    },
    "farewell": {
        "farewell": 0.9,
        "gratitude": 0.7,
        "information": 0.3
    }
}

# Default transition probabilities for intents not explicitly defined
DEFAULT_TRANSITIONS = {
    "question": 0.5,
    "statement": 0.5,
    "information": 0.4,
    "opinion": 0.3
}

# Domain-specific intent models
DOMAIN_INTENTS = {
    "data_analysis": [
        "analyze_data", "create_chart", "find_correlation", 
        "predict_trend", "summarize_data", "filter_data",
        "compare_datasets", "identify_outliers", "calculate_statistics"
    ],
    "web_search": [
        "search_web", "find_information", "research_topic",
        "get_news", "find_article", "check_fact"
    ],
    "system": [
        "change_settings", "update_preferences", "manage_account",
        "get_help", "report_issue", "check_status"
    ],
    "calendar": [
        "schedule_event", "check_availability", "set_reminder",
        "cancel_appointment", "reschedule_meeting", "find_time"
    ]
}

def recognize_intent_with_context(text: str, method: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recognize intent with contextual awareness
    
    Args:
        text: User input text
        method: Base method to use for intent recognition
        context: Contextual information including:
            - previous_intents: List of previous intents
            - conversation_history: Previous messages
            - user_profile: User profile information
            - current_topic: Current conversation topic
            
    Returns:
        Intent information with contextually adjusted confidence
    """
    # Get base intent recognition
    base_result = None
    if method == "ensemble":
        # Try multiple methods and combine results
        spacy_intent = get_intent_spacy(text)
        huggingface_result = get_intent_huggingface(text)
        rasa_result = get_intent_rasa(text)
        
        # Collect all intents with their confidence
        candidates = []
        if spacy_intent:
            candidates.append({"intent": spacy_intent, "confidence": 0.7, "method": "spacy"})
        if huggingface_result and huggingface_result.get("intent"):
            candidates.append(huggingface_result)
        if rasa_result and rasa_result.get("intent"):
            candidates.append(rasa_result)
            
        if candidates:
            # Use the highest confidence intent as base
            base_result = max(candidates, key=lambda x: x.get("confidence", 0))
        else:
            # Fallback to spaCy
            base_result = {"intent": spacy_intent, "confidence": 0.7, "method": "spacy"}
    elif method == "spacy":
        intent = get_intent_spacy(text)
        base_result = {"intent": intent, "confidence": 0.7, "method": "spacy"}
    elif method == "huggingface":
        result = get_intent_huggingface(text)
        if result:
            base_result = result
        else:
            # Fallback to spaCy
            intent = get_intent_spacy(text)
            base_result = {"intent": intent, "confidence": 0.5, "method": "spacy_fallback"}
    elif method == "rasa":
        result = get_intent_rasa(text)
        if result:
            base_result = result
        else:
            # Fallback to spaCy
            intent = get_intent_spacy(text)
            base_result = {"intent": intent, "confidence": 0.5, "method": "spacy_fallback"}
    
    # Apply contextual adjustments
    adjusted_result = adjust_intent_with_context(base_result, context)
    
    # Check for domain-specific intents based on current topic
    if context.get("current_topic") in DOMAIN_INTENTS:
        domain_result = check_domain_specific_intent(text, context["current_topic"])
        if domain_result and domain_result.get("confidence", 0) > adjusted_result.get("confidence", 0):
            return domain_result
    
    return adjusted_result

def adjust_intent_with_context(intent_result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adjust intent confidence based on conversation context
    
    Args:
        intent_result: Base intent recognition result
        context: Contextual information
        
    Returns:
        Adjusted intent result with updated confidence
    """
    if not intent_result or not context:
        return intent_result
    
    # Get the recognized intent and confidence
    intent = intent_result.get("intent", "")
    confidence = intent_result.get("confidence", 0.5)
    
    # Get previous intents if available
    previous_intents = context.get("previous_intents", [])
    
    # No adjustment needed if no previous intents
    if not previous_intents:
        return intent_result
    
    # Get the most recent intent
    last_intent = previous_intents[-1] if previous_intents else None
    
    # Adjust confidence based on intent transitions
    if last_intent:
        # Get transition probabilities for the last intent
        transitions = INTENT_TRANSITIONS.get(last_intent, DEFAULT_TRANSITIONS)
        
        # Get transition probability for the current intent
        transition_prob = transitions.get(intent, 0.2)  # Default low probability if not specified
        
        # Adjust confidence based on transition probability
        # Higher transition probability increases confidence
        adjusted_confidence = confidence * (1.0 + 0.5 * transition_prob)
        
        # Cap confidence at 0.95
        adjusted_confidence = min(adjusted_confidence, 0.95)
        
        # Update the result
        adjusted_result = intent_result.copy()
        adjusted_result["confidence"] = adjusted_confidence
        adjusted_result["context_adjusted"] = True
        adjusted_result["previous_intent"] = last_intent
        
        return adjusted_result
    
    return intent_result

def detect_multiple_intents(text: str, method: str) -> Dict[str, Any]:
    """
    Detect multiple intents in a single user message
    
    Args:
        text: User input text
        method: Base method for intent recognition
        
    Returns:
        Dict with primary intent and list of all detected intents
    """
    # Split text into potential segments (sentences or clauses)
    segments = split_into_segments(text)
    
    # If only one segment, use standard intent recognition
    if len(segments) <= 1:
        if method == "spacy":
            intent = get_intent_spacy(text)
            return {
                "intent": intent, 
                "confidence": 0.7, 
                "method": "spacy",
                "multi_intent": False,
                "all_intents": [{"intent": intent, "confidence": 0.7, "text": text}]
            }
        elif method == "huggingface":
            result = get_intent_huggingface(text)
            if result:
                result["multi_intent"] = False
                result["all_intents"] = [{"intent": result["intent"], "confidence": result["confidence"], "text": text}]
                return result
            # Fallback to spaCy
            intent = get_intent_spacy(text)
            return {
                "intent": intent, 
                "confidence": 0.5, 
                "method": "spacy_fallback",
                "multi_intent": False,
                "all_intents": [{"intent": intent, "confidence": 0.5, "text": text}]
            }
        elif method == "ensemble":
            # Use multiple methods and combine results
            spacy_intent = get_intent_spacy(text)
            huggingface_result = get_intent_huggingface(text)
            rasa_result = get_intent_rasa(text)
            
            # Collect all intents with their confidence
            candidates = []
            if spacy_intent:
                candidates.append({"intent": spacy_intent, "confidence": 0.7, "method": "spacy"})
            if huggingface_result and huggingface_result.get("intent"):
                candidates.append(huggingface_result)
            if rasa_result and rasa_result.get("intent"):
                candidates.append(rasa_result)
                
            if candidates:
                # Use the highest confidence intent as primary
                primary = max(candidates, key=lambda x: x.get("confidence", 0))
                primary["multi_intent"] = False
                primary["all_intents"] = [{"intent": primary["intent"], "confidence": primary["confidence"], "text": text}]
                return primary
            else:
                # Fallback to spaCy
                return {
                    "intent": spacy_intent, 
                    "confidence": 0.7, 
                    "method": "spacy",
                    "multi_intent": False,
                    "all_intents": [{"intent": spacy_intent, "confidence": 0.7, "text": text}]
                }
    
    # Process each segment to identify its intent
    segment_intents = []
    for segment in segments:
        segment_text = segment.strip()
        if not segment_text:
            continue
            
        # Use the specified method for each segment
        if method == "spacy":
            intent = get_intent_spacy(segment_text)
            segment_intents.append({
                "intent": intent,
                "confidence": 0.7,
                "method": "spacy",
                "text": segment_text
            })
        elif method == "huggingface":
            result = get_intent_huggingface(segment_text)
            if result and result.get("intent"):
                segment_intents.append({
                    "intent": result["intent"],
                    "confidence": result["confidence"],
                    "method": "huggingface",
                    "text": segment_text
                })
            else:
                # Fallback to spaCy
                intent = get_intent_spacy(segment_text)
                segment_intents.append({
                    "intent": intent,
                    "confidence": 0.5,
                    "method": "spacy_fallback",
                    "text": segment_text
                })
        elif method == "ensemble":
            # Try multiple methods for each segment
            spacy_intent = get_intent_spacy(segment_text)
            huggingface_result = get_intent_huggingface(segment_text)
            
            # Use the higher confidence result
            if huggingface_result and huggingface_result.get("confidence", 0) > 0.7:
                segment_intents.append({
                    "intent": huggingface_result["intent"],
                    "confidence": huggingface_result["confidence"],
                    "method": "huggingface",
                    "text": segment_text
                })
            else:
                segment_intents.append({
                    "intent": spacy_intent,
                    "confidence": 0.7,
                    "method": "spacy",
                    "text": segment_text
                })
    
    # If no intents were detected, fall back to single intent for the whole text
    if not segment_intents:
        intent = get_intent_spacy(text)
        return {
            "intent": intent, 
            "confidence": 0.7, 
            "method": "spacy",
            "multi_intent": False,
            "all_intents": [{"intent": intent, "confidence": 0.7, "text": text}]
        }
    
    # Find the primary intent (highest confidence or most important type)
    primary_intent = select_primary_intent(segment_intents)
    
    # Construct the result
    result = {
        "intent": primary_intent["intent"],
        "confidence": primary_intent["confidence"],
        "method": primary_intent["method"],
        "multi_intent": len(segment_intents) > 1,
        "all_intents": segment_intents
    }
    
    return result

def split_into_segments(text: str) -> List[str]:
    """
    Split text into segments for multi-intent detection
    
    Args:
        text: User input text
        
    Returns:
        List of text segments
    """
    # First try to split by sentence boundaries
    doc = nlp(text)
    sentences = [sent.text for sent in doc.sents]
    
    # If we have multiple sentences, return them
    if len(sentences) > 1:
        return sentences
    
    # Otherwise, try to split by conjunctions and punctuation
    segments = []
    
    # Split by common conjunctions and punctuation
    split_patterns = [
        r'(?<=[.!?])\s+',  # Split after end of sentence punctuation
        r'(?<=\w)(?:,\s+and\s+|\s+and\s+)',  # Split on "and" with optional comma
        r'(?<=\w)(?:,\s+but\s+|\s+but\s+)',  # Split on "but" with optional comma
        r'(?<=\w)(?:,\s+or\s+|\s+or\s+)',    # Split on "or" with optional comma
        r'(?<=\w)(?:;\s+)',  # Split on semicolons
    ]
    
    current_text = text
    for pattern in split_patterns:
        parts = re.split(pattern, current_text)
        if len(parts) > 1:
            segments.extend(parts)
            break
    
    # If no splits were made, return the original text as a single segment
    if not segments:
        segments = [text]
    
    return segments

def select_primary_intent(intents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Select the primary intent from multiple detected intents
    
    Args:
        intents: List of detected intents with confidence scores
        
    Returns:
        The primary intent
    """
    if not intents:
        return {"intent": "statement", "confidence": 0.5, "method": "default"}
    
    # Define priority order for intents (higher priority intents come first)
    priority_order = [
        "question",
        "request",
        "command",
        "information",
        "clarification",
        "confirmation",
        "greeting",
        "farewell",
        "gratitude",
        "opinion",
        "statement"
    ]
    
    # First, check for high confidence intents (above threshold)
    high_confidence = [i for i in intents if i.get("confidence", 0) > CONFIDENCE_THRESHOLD]
    if high_confidence:
        # Sort by priority order first, then by confidence
        for priority_intent in priority_order:
            priority_matches = [i for i in high_confidence if i.get("intent") == priority_intent]
            if priority_matches:
                return max(priority_matches, key=lambda x: x.get("confidence", 0))
        
        # If no priority matches, return the highest confidence intent
        return max(high_confidence, key=lambda x: x.get("confidence", 0))
    
    # If no high confidence intents, use priority order
    for priority_intent in priority_order:
        priority_matches = [i for i in intents if i.get("intent") == priority_intent]
        if priority_matches:
            return max(priority_matches, key=lambda x: x.get("confidence", 0))
    
    # Fallback to highest confidence intent
    return max(intents, key=lambda x: x.get("confidence", 0))

def check_domain_specific_intent(text: str, domain: str) -> Optional[Dict[str, Any]]:
    """
    Check for domain-specific intents
    
    Args:
        text: User input text
        domain: The current domain/topic
        
    Returns:
        Domain-specific intent if detected, None otherwise
    """
    if domain not in DOMAIN_INTENTS:
        return None
    
    domain_intent_list = DOMAIN_INTENTS[domain]
    text_lower = text.lower()
    
    # Check for domain-specific keywords and patterns
    for intent in domain_intent_list:
        # Convert intent name to keywords (e.g., "analyze_data" -> ["analyze", "data"])
        keywords = intent.replace("_", " ").split()
        
        # Check if all keywords are present in the text
        if all(keyword in text_lower for keyword in keywords):
            return {
                "intent": intent,
                "confidence": 0.8,  # High confidence for domain-specific match
                "method": "domain_specific",
                "domain": domain
            }
    
    # No domain-specific intent detected
    return None
