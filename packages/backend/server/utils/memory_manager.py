from models.db import db
from models.user_preference import UserPreference, MemorizedDetail
import re
from datetime import datetime
import nltk
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag

# Download NLTK resources (only needed once)
try:
    nltk.data.find('punkt')
    nltk.data.find('averaged_perceptron_tagger')
except LookupError:
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')

def extract_key_information(user_id, message_content):
    """
    Extract and store key information from user messages
    """
    try:
        # Find user preferences
        preferences = UserPreference.query.filter_by(user_id=user_id).first()
        
        if not preferences:
            preferences = UserPreference(user_id=user_id)
            db.session.add(preferences)
            db.session.commit()
        
        # Extract personal information
        extract_personal_info(preferences, message_content)
        
        # Extract preferences
        extract_preferences(preferences, message_content)
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error extracting key information: {str(e)}")

def extract_personal_info(preferences, message_content):
    """
    Extract personal information like name, age, location, etc.
    """
    # Name extraction
    name_patterns = [
        r"(?:my name is|I'm|I am|call me) (\w+)",
        r"(\w+) is my name"
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, message_content, re.IGNORECASE)
        if match:
            name = match.group(1)
            # Store only if it looks like a name (capitalized word)
            if name[0].isupper() and len(name) > 1:
                add_or_update_memory(preferences, "name", name)
    
    # Age extraction
    age_patterns = [
        r"(?:I am|I'm) (\d{1,2}) years old",
        r"my age is (\d{1,2})"
    ]
    
    for pattern in age_patterns:
        match = re.search(pattern, message_content, re.IGNORECASE)
        if match:
            age = match.group(1)
            # Validate age is reasonable
            if 1 <= int(age) <= 120:
                add_or_update_memory(preferences, "age", age)
    
    # Location extraction
    location_patterns = [
        r"(?:I live in|I'm from|I am from) ([A-Z][a-z]+(?: [A-Z][a-z]+)*)",
        r"(?:I'm in|I am in) ([A-Z][a-z]+(?: [A-Z][a-z]+)*)"
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, message_content)
        if match:
            location = match.group(1)
            add_or_update_memory(preferences, "location", location)
    
    # Occupation extraction
    occupation_patterns = [
        r"(?:I work as|I'm|I am) (?:a|an) ([a-z]+(?: [a-z]+)*)",
        r"(?:my job is|my profession is) (?:a|an)? ([a-z]+(?: [a-z]+)*)"
    ]
    
    for pattern in occupation_patterns:
        match = re.search(pattern, message_content, re.IGNORECASE)
        if match:
            occupation = match.group(1)
            # Filter out common non-occupation matches
            non_occupations = ["fine", "good", "okay", "ok", "alright", "well", "tired", "happy", "sad"]
            if occupation.lower() not in non_occupations and len(occupation) > 3:
                add_or_update_memory(preferences, "occupation", occupation)

def extract_preferences(preferences, message_content):
    """
    Extract user preferences from message content
    """
    # Like patterns
    like_patterns = [
        r"I (?:really |)like ([a-z]+(?: [a-z]+)*)",
        r"I (?:really |)love ([a-z]+(?: [a-z]+)*)",
        r"I (?:really |)enjoy ([a-z]+(?: [a-z]+)*)",
        r"([a-z]+(?: [a-z]+)*) is my favorite"
    ]
    
    for pattern in like_patterns:
        matches = re.finditer(pattern, message_content, re.IGNORECASE)
        for match in matches:
            liked_thing = match.group(1).lower()
            # Filter out common words
            common_words = ["it", "this", "that", "you", "to", "the", "a", "an"]
            if liked_thing not in common_words and len(liked_thing) > 2:
                add_or_update_memory(preferences, f"likes_{liked_thing}", "true")
    
    # Dislike patterns
    dislike_patterns = [
        r"I (?:really |)(?:don't|do not) like ([a-z]+(?: [a-z]+)*)",
        r"I (?:really |)hate ([a-z]+(?: [a-z]+)*)",
        r"I (?:really |)dislike ([a-z]+(?: [a-z]+)*)"
    ]
    
    for pattern in dislike_patterns:
        matches = re.finditer(pattern, message_content, re.IGNORECASE)
        for match in matches:
            disliked_thing = match.group(1).lower()
            # Filter out common words
            common_words = ["it", "this", "that", "you", "to", "the", "a", "an"]
            if disliked_thing not in common_words and len(disliked_thing) > 2:
                add_or_update_memory(preferences, f"dislikes_{disliked_thing}", "true")

def add_or_update_memory(preferences, key, value):
    """
    Add or update a memorized detail
    """
    # Check if the key already exists
    existing_detail = MemorizedDetail.query.filter_by(
        preference_id=preferences.id,
        key=key
    ).first()
    
    if existing_detail:
        # Update existing detail
        existing_detail.value = value
        existing_detail.timestamp = datetime.utcnow()
    else:
        # Add new detail
        new_detail = MemorizedDetail(
            preference_id=preferences.id,
            key=key,
            value=value
        )
        db.session.add(new_detail)
