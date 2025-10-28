"""
Advanced Entity Recognition Module

This module extends the basic entity recognition with:
1. Contextual entity resolution
2. Custom entity types
3. Entity linking to knowledge bases
4. Hierarchical entity recognition
5. Relationship extraction between entities
"""

import os
import re
import json
import numpy as np
from typing import List, Dict, Any, Tuple, Optional, Union
from collections import defaultdict
from pathlib import Path

# Import from base entity recognition
from nlp.entity_recognition import (
    extract_entities_spacy,
    extract_entities_nltk,
    extract_entities_huggingface,
    extract_custom_entities,
    extract_entities,
    link_entities,
    nlp
)

# Import advanced features configuration
sys_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if sys_path not in os.sys.path:
    os.sys.path.append(sys_path)

from config.advanced_features import NLP_CONFIG, is_feature_enabled

# Get entity recognition config
entity_config = NLP_CONFIG.get("entity_recognition", {})
CONFIDENCE_THRESHOLD = entity_config.get("confidence_threshold", 0.6)
CUSTOM_ENTITIES_ENABLED = entity_config.get("custom_entities", True)

# Load knowledge bases if available
KNOWLEDGE_BASE_DIR = Path(sys_path) / "data" / "knowledge_bases"
KNOWLEDGE_BASE_DIR.mkdir(exist_ok=True, parents=True)

# Entity types for relationship extraction
ENTITY_TYPES = {
    "PERSON": ["person", "people", "individual", "PER", "PERSON"],
    "ORGANIZATION": ["organization", "company", "corporation", "agency", "ORG", "ORGANIZATION"],
    "LOCATION": ["location", "place", "city", "country", "address", "LOC", "GPE", "LOCATION"],
    "DATE": ["date", "time", "datetime", "DATE", "TIME"],
    "EVENT": ["event", "happening", "occasion", "EVENT"],
    "PRODUCT": ["product", "item", "goods", "PRODUCT"],
    "WORK_OF_ART": ["artwork", "book", "movie", "song", "WORK_OF_ART"],
    "LAW": ["law", "regulation", "legislation", "LAW"],
    "LANGUAGE": ["language", "tongue", "dialect", "LANGUAGE"],
    "MONEY": ["money", "currency", "financial", "MONEY"],
    "QUANTITY": ["quantity", "amount", "measurement", "QUANTITY"],
    "PERCENT": ["percent", "percentage", "ratio", "PERCENT"],
    "CARDINAL": ["number", "numeric", "CARDINAL"],
    "ORDINAL": ["ordinal", "sequence", "ORDINAL"]
}

# Common relationships between entity types
ENTITY_RELATIONSHIPS = {
    ("PERSON", "ORGANIZATION"): ["works_for", "founded", "leads", "member_of", "affiliated_with"],
    ("PERSON", "LOCATION"): ["lives_in", "visited", "from", "born_in", "traveled_to"],
    ("PERSON", "PERSON"): ["related_to", "friend_of", "colleague_of", "married_to", "parent_of", "child_of", "sibling_of"],
    ("PERSON", "EVENT"): ["participated_in", "organized", "attended", "witnessed"],
    ("PERSON", "WORK_OF_ART"): ["created", "wrote", "directed", "performed_in", "produced"],
    ("ORGANIZATION", "LOCATION"): ["located_in", "headquartered_in", "operates_in", "founded_in"],
    ("ORGANIZATION", "ORGANIZATION"): ["subsidiary_of", "partner_of", "competitor_of", "acquired", "merged_with"],
    ("ORGANIZATION", "PRODUCT"): ["produces", "sells", "manufactures", "distributes", "developed"],
    ("ORGANIZATION", "EVENT"): ["organized", "sponsored", "participated_in", "hosted"],
    ("EVENT", "LOCATION"): ["held_in", "occurred_at", "took_place_in"],
    ("EVENT", "DATE"): ["occurred_on", "started_on", "ended_on", "scheduled_for"],
    ("PRODUCT", "ORGANIZATION"): ["made_by", "sold_by", "distributed_by"],
    ("WORK_OF_ART", "PERSON"): ["created_by", "written_by", "directed_by", "performed_by"]
}

# Relationship extraction patterns
RELATIONSHIP_PATTERNS = [
    # Person-Organization patterns
    (r"(\w+(?:\s\w+)*) works for (\w+(?:\s\w+)*)", "works_for", "PERSON", "ORGANIZATION"),
    (r"(\w+(?:\s\w+)*) founded (\w+(?:\s\w+)*)", "founded", "PERSON", "ORGANIZATION"),
    (r"(\w+(?:\s\w+)*) is (?:the )?(?:CEO|president|director|head|leader) of (\w+(?:\s\w+)*)", "leads", "PERSON", "ORGANIZATION"),
    
    # Person-Location patterns
    (r"(\w+(?:\s\w+)*) lives in (\w+(?:\s\w+)*)", "lives_in", "PERSON", "LOCATION"),
    (r"(\w+(?:\s\w+)*) is from (\w+(?:\s\w+)*)", "from", "PERSON", "LOCATION"),
    (r"(\w+(?:\s\w+)*) was born in (\w+(?:\s\w+)*)", "born_in", "PERSON", "LOCATION"),
    
    # Person-Person patterns
    (r"(\w+(?:\s\w+)*) is (?:the )?(?:brother|sister) of (\w+(?:\s\w+)*)", "sibling_of", "PERSON", "PERSON"),
    (r"(\w+(?:\s\w+)*) is (?:the )?(?:father|mother|parent) of (\w+(?:\s\w+)*)", "parent_of", "PERSON", "PERSON"),
    (r"(\w+(?:\s\w+)*) is (?:the )?(?:son|daughter|child) of (\w+(?:\s\w+)*)", "child_of", "PERSON", "PERSON"),
    (r"(\w+(?:\s\w+)*) is married to (\w+(?:\s\w+)*)", "married_to", "PERSON", "PERSON"),
    
    # Organization-Location patterns
    (r"(\w+(?:\s\w+)*) is (?:located|based) in (\w+(?:\s\w+)*)", "located_in", "ORGANIZATION", "LOCATION"),
    (r"(\w+(?:\s\w+)*) headquarters (?:is|are) in (\w+(?:\s\w+)*)", "headquartered_in", "ORGANIZATION", "LOCATION"),
    
    # Event-Date patterns
    (r"(\w+(?:\s\w+)*) (?:occurred|happened|took place) on (\w+(?:\s\w+)*)", "occurred_on", "EVENT", "DATE"),
    
    # Product-Organization patterns
    (r"(\w+(?:\s\w+)*) is made by (\w+(?:\s\w+)*)", "made_by", "PRODUCT", "ORGANIZATION"),
    (r"(\w+(?:\s\w+)*) produces (\w+(?:\s\w+)*)", "produces", "ORGANIZATION", "PRODUCT")
]

# Custom entity types with their patterns
CUSTOM_ENTITY_PATTERNS = {
    "EMAIL": [
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    ],
    "PHONE_NUMBER": [
        r'\b(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
        r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'
    ],
    "URL": [
        r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?:/[-\w%!$&\'()*+,;=:@/~]+)*(?:\?[-\w%!$&\'()*+,;=:@/~]*)?(?:#[-\w%!$&\'()*+,;=:@/~]*)?',
        r'www\.(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?:/[-\w%!$&\'()*+,;=:@/~]+)*(?:\?[-\w%!$&\'()*+,;=:@/~]*)?(?:#[-\w%!$&\'()*+,;=:@/~]*)?'
    ],
    "IP_ADDRESS": [
        r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    ],
    "CREDIT_CARD": [
        r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
        r'\b\d{16}\b'
    ],
    "SSN": [
        r'\b\d{3}-\d{2}-\d{4}\b'
    ],
    "USERNAME": [
        r'@\w+',
        r'u/\w+',
        r'r/\w+'
    ],
    "HASHTAG": [
        r'#\w+'
    ],
    "CURRENCY_AMOUNT": [
        r'\$\d+(?:\.\d{2})?',
        r'\€\d+(?:\.\d{2})?',
        r'\£\d+(?:\.\d{2})?',
        r'\¥\d+(?:\.\d{2})?'
    ],
    "PERCENTAGE": [
        r'\d+(?:\.\d+)?%'
    ],
    "MEASUREMENT": [
        r'\d+(?:\.\d+)?\s*(?:kg|g|mg|lb|oz|km|m|cm|mm|mi|ft|in|l|ml|gal|qt|pt|fl oz)'
    ],
    "TIME": [
        r'\b(?:1[0-2]|0?[1-9]):[0-5][0-9](?:\s*[ap]\.?m\.?)?',
        r'\b(?:2[0-3]|[01]?[0-9]):[0-5][0-9](?::[0-5][0-9])?'
    ],
    "DATE_MDY": [
        r'\b(?:0?[1-9]|1[0-2])/(?:0?[1-9]|[12][0-9]|3[01])/(?:19|20)?\d{2}\b'
    ],
    "DATE_DMY": [
        r'\b(?:0?[1-9]|[12][0-9]|3[01])/(?:0?[1-9]|1[0-2])/(?:19|20)?\d{2}\b'
    ],
    "DATE_YMD": [
        r'\b(?:19|20)\d{2}-(?:0?[1-9]|1[0-2])-(?:0?[1-9]|[12][0-9]|3[01])\b'
    ],
    "FILE_PATH": [
        r'(?:/|\\)(?:[-\w.]+(?:/|\\))*[-\w.]+',
        r'[A-Za-z]:\\(?:[-\w.]+\\)*[-\w.]+'
    ],
    "VERSION_NUMBER": [
        r'\b\d+(?:\.\d+){1,3}\b'
    ],
    "ISBN": [
        r'\b(?:ISBN(?:-1[03])?:?\s*)?(?=[-0-9xX ]{13}$|[-0-9xX ]{17}$|[-0-9xX ]{10}$)(?:97[89][-\s]?)?[0-9]{1,5}[-\s]?[0-9]{1,7}[-\s]?[0-9]{1,6}[-\s]?[0-9xX]\b'
    ]
}

def load_knowledge_bases():
    """Load available knowledge bases"""
    knowledge_bases = {}
    
    # Load all JSON files in the knowledge base directory
    for kb_file in KNOWLEDGE_BASE_DIR.glob("*.json"):
        try:
            with open(kb_file, "r", encoding="utf-8") as f:
                kb_data = json.load(f)
                knowledge_bases[kb_file.stem] = kb_data
        except Exception as e:
            print(f"Error loading knowledge base {kb_file}: {str(e)}")
    
    return knowledge_bases

# Load knowledge bases
KNOWLEDGE_BASES = load_knowledge_bases()

def extract_entities_with_context(text: str, context: Dict[str, Any] = None, methods: List[str] = None) -> List[Dict[str, Any]]:
    """
    Extract entities with contextual awareness
    
    Args:
        text: Text to extract entities from
        context: Contextual information including:
            - previous_entities: Previously extracted entities
            - conversation_history: Previous messages
            - user_profile: User profile information
            - current_topic: Current conversation topic
        methods: List of methods to use
        
    Returns:
        List of extracted entities with context-enhanced information
    """
    # Get base entities
    base_entities = extract_entities(text, methods)
    
    # If no context provided, return base entities
    if not context:
        return base_entities
    
    # Get previous entities if available
    previous_entities = context.get("previous_entities", [])
    
    # Resolve coreferences (pronouns and references)
    resolved_entities = resolve_coreferences(text, base_entities, previous_entities, context)
    
    # Enhance entities with additional context
    enhanced_entities = enhance_entities_with_context(resolved_entities, context)
    
    return enhanced_entities

def resolve_coreferences(text: str, entities: List[Dict[str, Any]], previous_entities: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Resolve coreferences (pronouns and references) in text
    
    Args:
        text: Text containing entities
        entities: Currently extracted entities
        previous_entities: Previously extracted entities
        context: Contextual information
        
    Returns:
        Entities with resolved coreferences
    """
    # Simple pronoun resolution
    pronouns = {
        "he": "PERSON",
        "she": "PERSON",
        "they": "PERSON",
        "it": "THING",
        "this": "THING",
        "that": "THING",
        "these": "THING",
        "those": "THING",
        "there": "LOCATION",
        "here": "LOCATION"
    }
    
    # Process the text with spaCy for linguistic features
    doc = nlp(text)
    
    # Find pronouns in the text
    pronoun_spans = []
    for token in doc:
        if token.lower_ in pronouns or token.pos_ == "PRON":
            pronoun_spans.append({
                "text": token.text,
                "start": token.idx,
                "end": token.idx + len(token.text),
                "type": pronouns.get(token.lower_, "THING")
            })
    
    # Try to resolve each pronoun
    resolved_entities = entities.copy()
    
    for pronoun in pronoun_spans:
        # Find the most recent matching entity from previous entities
        candidates = [
            e for e in previous_entities 
            if any(t in ENTITY_TYPES.get(pronoun["type"], []) for t in ENTITY_TYPES.keys())
        ]
        
        if candidates:
            # Sort by recency (assuming previous_entities is ordered by recency)
            most_recent = candidates[0]
            
            # Add a resolved entity
            resolved_entities.append({
                "text": most_recent["text"],
                "label": most_recent["label"],
                "start": pronoun["start"],
                "end": pronoun["end"],
                "method": "coreference",
                "original_text": pronoun["text"],
                "confidence": 0.7
            })
    
    return resolved_entities

def enhance_entities_with_context(entities: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Enhance entities with additional contextual information
    
    Args:
        entities: Extracted entities
        context: Contextual information
        
    Returns:
        Enhanced entities
    """
    enhanced = []
    
    # Get user profile if available
    user_profile = context.get("user_profile", {})
    
    for entity in entities:
        # Create a copy to enhance
        enhanced_entity = entity.copy()
        
        # Add confidence if not present
        if "confidence" not in enhanced_entity:
            enhanced_entity["confidence"] = 0.8
        
        # Check if entity is related to user profile
        if user_profile:
            for key, value in user_profile.items():
                if isinstance(value, str) and entity["text"].lower() in value.lower():
                    enhanced_entity["related_to_user"] = True
                    enhanced_entity["user_relation"] = key
                    enhanced_entity["confidence"] = 0.9  # Higher confidence for user-related entities
        
        # Link to knowledge bases if available
        if KNOWLEDGE_BASES:
            for kb_name, kb_data in KNOWLEDGE_BASES.items():
                for kb_entity in kb_data.get("entities", []):
                    if entity["text"].lower() == kb_entity.get("name", "").lower():
                        enhanced_entity["knowledge_base"] = kb_name
                        enhanced_entity["kb_entity_id"] = kb_entity.get("id")
                        enhanced_entity["kb_entity_type"] = kb_entity.get("type")
                        enhanced_entity["kb_entity_data"] = kb_entity
                        enhanced_entity["confidence"] = 0.95  # Very high confidence for KB matches
        
        enhanced.append(enhanced_entity)
    
    return enhanced

def extract_hierarchical_entities(text: str, methods: List[str] = None) -> Dict[str, Any]:
    """
    Extract hierarchical entities with relationships
    
    Args:
        text: Text to extract entities from
        methods: List of methods to use
        
    Returns:
        Hierarchical structure of entities with relationships
    """
    # Get flat list of entities
    entities = extract_entities(text, methods)
    
    # Extract relationships between entities
    relationships = extract_entity_relationships(text, entities)
    
    # Group entities by type
    entities_by_type = defaultdict(list)
    for entity in entities:
        entity_type = entity["label"]
        # Normalize entity type to standard categories
        for standard_type, aliases in ENTITY_TYPES.items():
            if entity_type in aliases:
                entity_type = standard_type
                break
        entities_by_type[entity_type].append(entity)
    
    # Create hierarchical structure
    hierarchy = {
        "entities": entities_by_type,
        "relationships": relationships,
        "text": text
    }
    
    return hierarchy

def extract_entity_relationships(text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract relationships between entities
    
    Args:
        text: Text containing entities
        entities: Extracted entities
        
    Returns:
        List of relationships between entities
    """
    relationships = []
    
    # Create a mapping of entity text to entity object for quick lookup
    entity_map = {}
    for entity in entities:
        entity_map[entity["text"].lower()] = entity
    
    # Check for relationship patterns
    for pattern, relation_type, source_type, target_type in RELATIONSHIP_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            source_text = match.group(1).strip().lower()
            target_text = match.group(2).strip().lower()
            
            # Find the entities that match the source and target text
            source_entity = None
            target_entity = None
            
            # Look for exact matches first
            if source_text in entity_map:
                source_entity = entity_map[source_text]
            if target_text in entity_map:
                target_entity = entity_map[target_text]
            
            # If not found, look for partial matches
            if not source_entity:
                for entity_text, entity in entity_map.items():
                    if source_text in entity_text or entity_text in source_text:
                        source_entity = entity
                        break
            
            if not target_entity:
                for entity_text, entity in entity_map.items():
                    if target_text in entity_text or entity_text in target_text:
                        target_entity = entity
                        break
            
            # If both entities found, add the relationship
            if source_entity and target_entity:
                relationship = {
                    "source": source_entity["text"],
                    "source_type": source_entity["label"],
                    "target": target_entity["text"],
                    "target_type": target_entity["label"],
                    "relation": relation_type,
                    "confidence": 0.8,
                    "method": "pattern_matching"
                }
                relationships.append(relationship)
    
    # Check for proximity-based relationships
    # Entities that appear close to each other may be related
    for i, entity1 in enumerate(entities):
        for j, entity2 in enumerate(entities[i+1:i+4]):  # Check next 3 entities
            entity1_type = entity1["label"]
            entity2_type = entity2["label"]
            
            # Normalize entity types
            for standard_type, aliases in ENTITY_TYPES.items():
                if entity1_type in aliases:
                    entity1_type = standard_type
                if entity2_type in aliases:
                    entity2_type = standard_type
            
            # Check if this entity pair has predefined relationships
            if (entity1_type, entity2_type) in ENTITY_RELATIONSHIPS:
                # Use a generic relationship if specific one can't be determined
                relation = ENTITY_RELATIONSHIPS[(entity1_type, entity2_type)][0]
                
                # Check if entities are close to each other in text
                distance = abs(entity1["start"] - entity2["start"])
                if distance < 50:  # If entities are within 50 characters
                    relationship = {
                        "source": entity1["text"],
                        "source_type": entity1["label"],
                        "target": entity2["text"],
                        "target_type": entity2["label"],
                        "relation": relation,
                        "confidence": 0.6,  # Lower confidence for proximity-based relationships
                        "method": "proximity"
                    }
                    relationships.append(relationship)
    
    return relationships

def extract_custom_entity_types(text: str) -> List[Dict[str, Any]]:
    """
    Extract custom entity types using regex patterns
    
    Args:
        text: Text to extract entities from
        
    Returns:
        List of custom entities
    """
    if not CUSTOM_ENTITIES_ENABLED:
        return []
    
    custom_entities = []
    
    # Check each custom entity type
    for entity_type, patterns in CUSTOM_ENTITY_PATTERNS.items():
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                start = match.start()
                end = match.end()
                entity_text = text[start:end]
                
                custom_entities.append({
                    "text": entity_text,
                    "label": entity_type,
                    "start": start,
                    "end": end,
                    "method": "custom_regex",
                    "confidence": 0.9  # High confidence for regex matches
                })
    
    return custom_entities

def anonymize_sensitive_entities(text: str, entities: List[Dict[str, Any]] = None) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Anonymize sensitive entities in text
    
    Args:
        text: Text containing sensitive entities
        entities: Pre-extracted entities (optional)
        
    Returns:
        Tuple of (anonymized text, list of anonymized entities)
    """
    # Extract entities if not provided
    if entities is None:
        entities = extract_entities(text, methods=["spacy", "regex"])
        
        # Add custom entities that might be sensitive
        custom_entities = extract_custom_entity_types(text)
        entities.extend(custom_entities)
    
    # Define sensitive entity types
    sensitive_types = [
        "PERSON", "EMAIL", "PHONE_NUMBER", "CREDIT_CARD", "SSN", 
        "ADDRESS", "DATE_OF_BIRTH", "IP_ADDRESS", "USERNAME"
    ]
    
    # Sort entities by start position (reversed to avoid text position shifts)
    sorted_entities = sorted(entities, key=lambda e: e["start"], reverse=True)
    
    # Create a copy of the text to modify
    anonymized_text = text
    anonymized_entities = []
    
    for entity in sorted_entities:
        entity_type = entity["label"]
        
        # Check if this entity type should be anonymized
        if entity_type in sensitive_types:
            # Create anonymized version
            anonymized_entity = entity.copy()
            
            # Replace with placeholder
            placeholder = f"[{entity_type}]"
            start = entity["start"]
            end = entity["end"]
            
            # Replace in the text
            anonymized_text = anonymized_text[:start] + placeholder + anonymized_text[end:]
            
            # Update entity information
            anonymized_entity["anonymized"] = True
            anonymized_entity["original_text"] = entity["text"]
            anonymized_entity["text"] = placeholder
            
            anonymized_entities.append(anonymized_entity)
        else:
            # Keep non-sensitive entities as is
            anonymized_entities.append(entity)
    
    return anonymized_text, anonymized_entities


class AdvancedEntityRecognition:
    """Lightweight wrapper class providing a simple interface expected by
    the rest of the application. When the full advanced pipeline is
    available, this can be expanded to include more context-aware features.
    """
    def __init__(self, config: Dict[str, Any] = None, memory_manager=None):
        self.config = config or {}
        self.memory_manager = memory_manager

    def extract_entities(self, text: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        # Use the context-aware extractor if possible, otherwise fall back
        return extract_entities_with_context(text, context=context)

    def anonymize(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        entities = extract_entities(text)
        return anonymize_sensitive_entities(text, entities)
