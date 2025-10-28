import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from textblob import TextBlob
from transformers import pipeline
import spacy
import re

# Download NLTK resources if needed
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')

# Load SpaCy model
try:
    nlp = spacy.load("en_core_web_md")
except OSError:
    # Download if not available
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_md"])
    nlp = spacy.load("en_core_web_md")

# Initialize HuggingFace emotion recognition pipeline
emotion_pipeline = None

def initialize_emotion_pipeline():
    """Initialize the HuggingFace emotion recognition pipeline"""
    global emotion_pipeline
    try:
        emotion_pipeline = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base")
    except Exception as e:
        print(f"Error initializing emotion pipeline: {str(e)}")

def analyze_sentiment_nltk(text):
    """Analyze sentiment using NLTK's VADER"""
    sid = SentimentIntensityAnalyzer()
    scores = sid.polarity_scores(text)
    
    # Determine sentiment category based on compound score
    if scores['compound'] >= 0.05:
        sentiment = "positive"
    elif scores['compound'] <= -0.05:
        sentiment = "negative"
    else:
        sentiment = "neutral"
    
    return {
        "sentiment": sentiment,
        "scores": scores,
        "method": "nltk_vader"
    }

def analyze_sentiment_textblob(text):
    """Analyze sentiment using TextBlob"""
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity
    
    # Determine sentiment category
    if polarity > 0.1:
        sentiment = "positive"
    elif polarity < -0.1:
        sentiment = "negative"
    else:
        sentiment = "neutral"
    
    return {
        "sentiment": sentiment,
        "polarity": polarity,
        "subjectivity": subjectivity,
        "method": "textblob"
    }

def analyze_emotion_huggingface(text):
    """Analyze emotion using HuggingFace transformers"""
    global emotion_pipeline
    
    if emotion_pipeline is None:
        initialize_emotion_pipeline()
        if emotion_pipeline is None:
            return None
    
    try:
        result = emotion_pipeline(text)
        
        # Map the emotion label
        emotion_label = result[0]['label']
        
        # Get the confidence score
        confidence = result[0]['score']
        
        return {
            "emotion": emotion_label,
            "confidence": confidence,
            "method": "huggingface"
        }
    except Exception as e:
        print(f"Error in emotion analysis: {str(e)}")
        return None

def analyze_emotion_keyword(text):
    """Analyze emotion using keyword-based approach"""
    text = text.lower()
    
    # Emotion keywords dictionary
    emotion_keywords = {
        "joy": ["happy", "joy", "delighted", "thrilled", "excited", "glad", "pleased", "wonderful", "fantastic", "awesome"],
        "sadness": ["sad", "unhappy", "depressed", "down", "miserable", "heartbroken", "grief", "sorrow", "disappointed"],
        "anger": ["angry", "mad", "furious", "outraged", "annoyed", "irritated", "frustrated", "hate", "resent"],
        "fear": ["afraid", "scared", "frightened", "terrified", "anxious", "worried", "nervous", "panic", "dread"],
        "surprise": ["surprised", "amazed", "astonished", "shocked", "stunned", "unexpected", "wow"],
        "disgust": ["disgusted", "revolted", "gross", "ew", "yuck", "nasty", "repulsed"],
        "love": ["love", "adore", "cherish", "affection", "fond", "care", "devoted"],
        "neutral": []  # Default if no emotion is detected
    }
    
    # Count emotion keywords
    emotion_counts = {emotion: 0 for emotion in emotion_keywords}
    
    for emotion, keywords in emotion_keywords.items():
        for keyword in keywords:
            # Use word boundaries to match whole words
            pattern = r'\b' + re.escape(keyword) + r'\b'
            matches = re.findall(pattern, text)
            emotion_counts[emotion] += len(matches)
    
    # Determine the dominant emotion
    if sum(emotion_counts.values()) == 0:
        dominant_emotion = "neutral"
    else:
        dominant_emotion = max(emotion_counts, key=emotion_counts.get)
    
    return {
        "emotion": dominant_emotion,
        "counts": emotion_counts,
        "method": "keyword"
    }

def analyze_sentiment_and_emotion(text, methods=None):
    """
    Analyze sentiment and emotion in text using multiple methods
    
    Args:
        text (str): Text to analyze
        methods (list): List of methods to use, options: "nltk", "textblob", "huggingface", "keyword", "all"
        
    Returns:
        dict: Sentiment and emotion analysis results
    """
    if methods is None:
        methods = ["nltk", "textblob", "keyword"]  # Default methods
    
    if "all" in methods:
        methods = ["nltk", "textblob", "huggingface", "keyword"]
    
    results = {
        "text": text,
        "sentiment": {},
        "emotion": {}
    }
    
    # Sentiment analysis
    if "nltk" in methods:
        results["sentiment"]["nltk"] = analyze_sentiment_nltk(text)
    
    if "textblob" in methods:
        results["sentiment"]["textblob"] = analyze_sentiment_textblob(text)
    
    # Emotion analysis
    if "huggingface" in methods:
        emotion_result = analyze_emotion_huggingface(text)
        if emotion_result:
            results["emotion"]["huggingface"] = emotion_result
    
    if "keyword" in methods:
        results["emotion"]["keyword"] = analyze_emotion_keyword(text)
    
    # Aggregate results
    sentiments = []
    for method, result in results["sentiment"].items():
        if result and "sentiment" in result:
            sentiments.append(result["sentiment"])
    
    emotions = []
    for method, result in results["emotion"].items():
        if result and "emotion" in result:
            emotions.append(result["emotion"])
    
    # Determine the most common sentiment
    if sentiments:
        from collections import Counter
        sentiment_counter = Counter(sentiments)
        results["dominant_sentiment"] = sentiment_counter.most_common(1)[0][0]
    else:
        results["dominant_sentiment"] = "neutral"
    
    # Determine the most common emotion
    if emotions:
        from collections import Counter
        emotion_counter = Counter(emotions)
        results["dominant_emotion"] = emotion_counter.most_common(1)[0][0]
    else:
        results["dominant_emotion"] = "neutral"
    
    return results

def get_emotional_intensity(text):
    """
    Measure the emotional intensity of the text
    Returns: float between 0 (neutral) and 1 (very intense)
    """
    # TextBlob subjectivity as a measure of emotional content
    blob = TextBlob(text)
    subjectivity = blob.sentiment.subjectivity
    
    # VADER intensity
    sid = SentimentIntensityAnalyzer()
    vader_scores = sid.polarity_scores(text)
    
    # Calculate intensity as the absolute value of compound score
    # combined with subjectivity
    intensity = (abs(vader_scores['compound']) + subjectivity) / 2
    
    return intensity

def analyze_user_sentiment(text):
    """
    Analyze the sentiment of user's message using multiple techniques
    Returns: 'positive', 'negative', or 'neutral'
    """
    results = analyze_sentiment_and_emotion(text)
    return results["dominant_sentiment"]


def analyze_sentiment(text):
    """Compatibility wrapper expected by some controllers.

    Returns a simple sentiment label: 'positive', 'negative', or 'neutral'.
    """
    return analyze_user_sentiment(text)
