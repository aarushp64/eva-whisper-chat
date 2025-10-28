from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer
import nltk
from nltk.tokenize import sent_tokenize
import re
import os

# Initialize translation pipelines
translation_pipelines = {}

# Language codes and names
LANGUAGE_CODES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
    "ru": "Russian",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "ar": "Arabic",
    "hi": "Hindi"
}

def get_translation_pipeline(source_lang, target_lang):
    """
    Get or initialize a translation pipeline for the given language pair
    
    Args:
        source_lang (str): Source language code
        target_lang (str): Target language code
        
    Returns:
        pipeline: HuggingFace translation pipeline
    """
    # Create a key for the language pair
    key = f"{source_lang}-{target_lang}"
    
    # Check if pipeline already exists
    if key in translation_pipelines:
        return translation_pipelines[key]
    
    try:
        # Initialize the translation pipeline
        if source_lang == "en" and target_lang in LANGUAGE_CODES:
            # English to X
            model_name = f"Helsinki-NLP/opus-mt-en-{target_lang}"
            translation_pipelines[key] = pipeline("translation", model=model_name)
        elif target_lang == "en" and source_lang in LANGUAGE_CODES:
            # X to English
            model_name = f"Helsinki-NLP/opus-mt-{source_lang}-en"
            translation_pipelines[key] = pipeline("translation", model=model_name)
        else:
            # X to Y (use English as intermediate)
            # This is not ideal but works for demonstration
            print(f"Direct translation from {source_lang} to {target_lang} not available. Using English as intermediate.")
            return None
        
        return translation_pipelines[key]
    except Exception as e:
        print(f"Error initializing translation pipeline {source_lang}-{target_lang}: {str(e)}")
        return None

def detect_language(text):
    """
    Detect the language of the given text
    
    Args:
        text (str): Text to detect language for
        
    Returns:
        str: Detected language code
    """
    try:
        # Try to use langdetect if available
        from langdetect import detect
        return detect(text)
    except ImportError:
        # Fallback to simple heuristic
        # This is a very basic approach and should be replaced with a proper language detection model
        common_words = {
            "en": ["the", "and", "is", "in", "to", "it", "of", "that", "you", "for"],
            "es": ["el", "la", "de", "que", "y", "en", "un", "ser", "se", "no"],
            "fr": ["le", "la", "de", "et", "est", "en", "un", "que", "qui", "pas"],
            "de": ["der", "die", "das", "und", "ist", "in", "zu", "den", "mit", "nicht"],
            "it": ["il", "la", "di", "e", "che", "è", "un", "per", "non", "sono"],
            "pt": ["o", "a", "de", "que", "e", "do", "da", "em", "um", "para"]
        }
        
        # Convert text to lowercase and tokenize
        text = text.lower()
        words = re.findall(r'\b\w+\b', text)
        
        # Count occurrences of common words for each language
        scores = {lang: 0 for lang in common_words}
        
        for word in words:
            for lang, common_word_list in common_words.items():
                if word in common_word_list:
                    scores[lang] += 1
        
        # Return the language with the highest score
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        # Default to English if no language is detected
        return "en"

def translate_text(text, target_lang="en", source_lang=None):
    """
    Translate text to the target language
    
    Args:
        text (str): Text to translate
        target_lang (str): Target language code
        source_lang (str): Source language code (if None, will be auto-detected)
        
    Returns:
        dict: Translation information including translated text and detected languages
    """
    # Check if text is empty
    if not text or text.strip() == "":
        return {
            "translated_text": "",
            "source_lang": None,
            "target_lang": target_lang,
            "method": "none"
        }
    
    # Detect source language if not provided
    if source_lang is None:
        source_lang = detect_language(text)
    
    # If source and target languages are the same, return the original text
    if source_lang == target_lang:
        return {
            "translated_text": text,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "method": "none"
        }
    
    # Get the translation pipeline
    pipeline = get_translation_pipeline(source_lang, target_lang)
    
    if pipeline is None:
        # Try using English as an intermediate language
        if source_lang != "en" and target_lang != "en":
            # First translate to English
            en_result = translate_text(text, "en", source_lang)
            
            if en_result and "translated_text" in en_result:
                # Then translate from English to target language
                final_result = translate_text(en_result["translated_text"], target_lang, "en")
                
                if final_result and "translated_text" in final_result:
                    return {
                        "translated_text": final_result["translated_text"],
                        "source_lang": source_lang,
                        "target_lang": target_lang,
                        "intermediate_lang": "en",
                        "method": "cascade"
                    }
        
        # If cascade translation failed or isn't applicable, try OpenAI if available
        if os.environ.get("OPENAI_API_KEY"):
            try:
                import openai
                
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": f"You are a translator. Translate the following text from {LANGUAGE_CODES.get(source_lang, source_lang)} to {LANGUAGE_CODES.get(target_lang, target_lang)}. Provide only the translated text without any explanations."},
                        {"role": "user", "content": text}
                    ],
                    temperature=0.3
                )
                
                translated_text = response.choices[0].message.content.strip()
                
                return {
                    "translated_text": translated_text,
                    "source_lang": source_lang,
                    "target_lang": target_lang,
                    "method": "openai"
                }
            except Exception as e:
                print(f"Error in OpenAI translation: {str(e)}")
        
        # If all else fails, return the original text
        return {
            "translated_text": text,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "error": "Translation not available for this language pair",
            "method": "none"
        }
    
    try:
        # Split text into sentences to handle long texts
        sentences = sent_tokenize(text)
        translated_sentences = []
        
        for sentence in sentences:
            # Skip empty sentences
            if not sentence.strip():
                translated_sentences.append("")
                continue
            
            # Translate the sentence
            translation = pipeline(sentence, max_length=512)
            
            # Extract the translated text
            translated_sentence = translation[0]["translation_text"]
            translated_sentences.append(translated_sentence)
        
        # Combine the translated sentences
        translated_text = " ".join(translated_sentences)
        
        return {
            "translated_text": translated_text,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "method": "huggingface"
        }
    except Exception as e:
        print(f"Error in translation: {str(e)}")
        
        # Try OpenAI as fallback if available
        if os.environ.get("OPENAI_API_KEY"):
            try:
                import openai
                
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": f"You are a translator. Translate the following text from {LANGUAGE_CODES.get(source_lang, source_lang)} to {LANGUAGE_CODES.get(target_lang, target_lang)}. Provide only the translated text without any explanations."},
                        {"role": "user", "content": text}
                    ],
                    temperature=0.3
                )
                
                translated_text = response.choices[0].message.content.strip()
                
                return {
                    "translated_text": translated_text,
                    "source_lang": source_lang,
                    "target_lang": target_lang,
                    "method": "openai_fallback"
                }
            except Exception as e:
                print(f"Error in OpenAI fallback translation: {str(e)}")
        
        # If all else fails, return the original text
        return {
            "translated_text": text,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "error": str(e),
            "method": "none"
        }

def get_supported_languages():
    """
    Get a list of supported languages for translation
    
    Returns:
        dict: Dictionary of supported language codes and names
    """
    return LANGUAGE_CODES
