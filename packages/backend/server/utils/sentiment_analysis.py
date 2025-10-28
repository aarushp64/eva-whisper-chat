from textblob import TextBlob
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Download NLTK resources (only needed once)
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')

def analyze_user_sentiment(text):
    """
    Analyze the sentiment of user's message using multiple techniques
    Returns: 'positive', 'negative', or 'neutral'
    """
    # TextBlob analysis
    blob = TextBlob(text)
    textblob_polarity = blob.sentiment.polarity
    
    # VADER analysis
    sid = SentimentIntensityAnalyzer()
    vader_scores = sid.polarity_scores(text)
    vader_compound = vader_scores['compound']
    
    # Combine the scores (simple average)
    # VADER compound score ranges from -1 to 1
    # TextBlob polarity ranges from -1 to 1
    combined_score = (textblob_polarity + vader_compound) / 2
    
    # Determine sentiment category
    if combined_score > 0.1:
        return 'positive'
    elif combined_score < -0.1:
        return 'negative'
    else:
        return 'neutral'

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
