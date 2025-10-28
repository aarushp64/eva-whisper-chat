import spacy
from transformers import pipeline
import nltk
from nltk.tokenize import word_tokenize
from nltk.chunk import ne_chunk
import re

# Download NLTK resources if needed
try:
    nltk.data.find('punkt')
    nltk.data.find('maxent_ne_chunker')
    nltk.data.find('words')
except LookupError:
    nltk.download('punkt')
    nltk.download('maxent_ne_chunker')
    nltk.download('words')

# Load SpaCy model
try:
    nlp = spacy.load("en_core_web_md")
except OSError:
    # Download if not available
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_md"])
    nlp = spacy.load("en_core_web_md")

# Initialize HuggingFace NER pipeline
ner_pipeline = None

def initialize_huggingface_ner():
    """Initialize the HuggingFace NER pipeline"""
    global ner_pipeline
    try:
        ner_pipeline = pipeline("ner", model="dslim/bert-base-NER")
    except Exception as e:
        print(f"Error initializing HuggingFace NER: {str(e)}")

def extract_entities_spacy(text):
    """Extract entities using SpaCy"""
    doc = nlp(text)
    entities = []
    
    for ent in doc.ents:
        entities.append({
            "text": ent.text,
            "label": ent.label_,
            "start": ent.start_char,
            "end": ent.end_char,
            "method": "spacy"
        })
    
    return entities

def extract_entities_nltk(text):
    """Extract entities using NLTK"""
    tokens = word_tokenize(text)
    pos_tags = nltk.pos_tag(tokens)
    named_entities = ne_chunk(pos_tags)
    
    entities = []
    current_entity = []
    current_type = None
    
    # Process the tree to extract named entities
    for chunk in named_entities:
        if hasattr(chunk, 'label'):
            entity_type = chunk.label()
            entity_text = ' '.join([token for token, pos in chunk.leaves()])
            
            # Find start and end positions in original text
            start = text.find(entity_text)
            if start >= 0:
                end = start + len(entity_text)
                entities.append({
                    "text": entity_text,
                    "label": entity_type,
                    "start": start,
                    "end": end,
                    "method": "nltk"
                })
    
    return entities

def extract_entities_huggingface(text):
    """Extract entities using HuggingFace transformers"""
    global ner_pipeline
    
    if ner_pipeline is None:
        initialize_huggingface_ner()
        if ner_pipeline is None:
            return []
    
    try:
        # Run NER
        ner_results = ner_pipeline(text)
        
        # Process results
        entities = []
        current_entity = {"text": "", "label": "", "start": 0, "end": 0}
        
        for token in ner_results:
            # Check if this is a continuation of the previous entity
            if token["entity"].startswith("B-"):
                # If we were building an entity, add it to the list
                if current_entity["text"]:
                    entities.append({**current_entity, "method": "huggingface"})
                
                # Start a new entity
                current_entity = {
                    "text": token["word"].replace("##", ""),
                    "label": token["entity"][2:],  # Remove B- prefix
                    "start": token["start"],
                    "end": token["end"],
                }
            elif token["entity"].startswith("I-") and current_entity["text"]:
                # Continue the current entity
                current_entity["text"] += token["word"].replace("##", "")
                current_entity["end"] = token["end"]
        
        # Add the last entity if there is one
        if current_entity["text"]:
            entities.append({**current_entity, "method": "huggingface"})
        
        return entities
    except Exception as e:
        print(f"Error in HuggingFace entity extraction: {str(e)}")
        return []

def extract_custom_entities(text):
    """Extract custom entity types using regex patterns"""
    entities = []
    
    # Email addresses
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    for match in re.finditer(email_pattern, text):
        entities.append({
            "text": match.group(),
            "label": "EMAIL",
            "start": match.start(),
            "end": match.end(),
            "method": "regex"
        })
    
    # Phone numbers (various formats)
    phone_patterns = [
        r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # 123-456-7890
        r'\b\(\d{3}\)[-.\s]?\d{3}[-.\s]?\d{4}\b',  # (123) 456-7890
        r'\b\+\d{1,3}[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'  # +1 123-456-7890
    ]
    
    for pattern in phone_patterns:
        for match in re.finditer(pattern, text):
            entities.append({
                "text": match.group(),
                "label": "PHONE",
                "start": match.start(),
                "end": match.end(),
                "method": "regex"
            })
    
    # URLs
    url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*(?:\?\S+)?'
    for match in re.finditer(url_pattern, text):
        entities.append({
            "text": match.group(),
            "label": "URL",
            "start": match.start(),
            "end": match.end(),
            "method": "regex"
        })
    
    # Dates (various formats)
    date_patterns = [
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY or DD/MM/YYYY
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',  # Month DD, YYYY
        r'\b\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b'  # DD Month YYYY
    ]
    
    for pattern in date_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            entities.append({
                "text": match.group(),
                "label": "DATE",
                "start": match.start(),
                "end": match.end(),
                "method": "regex"
            })
    
    # Time
    time_pattern = r'\b(?:1[0-2]|0?[1-9]):[0-5][0-9](?:\s?[ap]\.?m\.?)?(?:\s?[A-Za-z]{3})?|\b(?:2[0-3]|[01]?[0-9]):[0-5][0-9](?:\s?hrs)?'
    for match in re.finditer(time_pattern, text, re.IGNORECASE):
        entities.append({
            "text": match.group(),
            "label": "TIME",
            "start": match.start(),
            "end": match.end(),
            "method": "regex"
        })
    
    # Money/currency
    money_pattern = r'\$\s?\d+(?:\.\d{2})?|\d+\s?(?:dollars|USD|EUR|GBP|JPY|INR)'
    for match in re.finditer(money_pattern, text, re.IGNORECASE):
        entities.append({
            "text": match.group(),
            "label": "MONEY",
            "start": match.start(),
            "end": match.end(),
            "method": "regex"
        })
    
    return entities

def extract_entities(text, methods=None):
    """
    Extract entities from text using multiple methods
    
    Args:
        text (str): Text to extract entities from
        methods (list): List of methods to use, options: "spacy", "nltk", "huggingface", "regex", "all"
        
    Returns:
        list: List of extracted entities with their types and positions
    """
    if methods is None:
        methods = ["spacy", "regex"]  # Default methods
    
    if "all" in methods:
        methods = ["spacy", "nltk", "huggingface", "regex"]
    
    all_entities = []
    
    if "spacy" in methods:
        all_entities.extend(extract_entities_spacy(text))
    
    if "nltk" in methods:
        all_entities.extend(extract_entities_nltk(text))
    
    if "huggingface" in methods:
        all_entities.extend(extract_entities_huggingface(text))
    
    if "regex" in methods:
        all_entities.extend(extract_custom_entities(text))
    
    # Remove duplicates (entities with same text and label)
    unique_entities = []
    seen = set()
    
    for entity in all_entities:
        key = (entity["text"], entity["label"])
        if key not in seen:
            seen.add(key)
            unique_entities.append(entity)
    
    return unique_entities

def link_entities(entities, knowledge_base=None):
    """
    Link extracted entities to knowledge base entries
    
    Args:
        entities (list): List of extracted entities
        knowledge_base (dict): Knowledge base to link entities to
        
    Returns:
        list: List of entities with added links to knowledge base
    """
    # If no knowledge base is provided, return entities as is
    if knowledge_base is None:
        return entities
    
    linked_entities = []
    
    for entity in entities:
        # Create a copy of the entity
        linked_entity = entity.copy()
        
        # Try to find the entity in the knowledge base
        entity_text = entity["text"].lower()
        
        # Check for exact matches
        if entity_text in knowledge_base:
            linked_entity["kb_link"] = knowledge_base[entity_text]
        else:
            # Check for partial matches
            for kb_entity, kb_data in knowledge_base.items():
                if entity_text in kb_entity.lower() or kb_entity.lower() in entity_text:
                    linked_entity["kb_link"] = kb_data
                    linked_entity["kb_match_type"] = "partial"
                    break
        
        linked_entities.append(linked_entity)
    
    return linked_entities
