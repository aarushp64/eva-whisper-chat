from transformers import pipeline
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.cluster.util import cosine_distance
import numpy as np
import networkx as nx
import re
import spacy

# Download NLTK resources if needed
try:
    nltk.data.find('punkt')
    nltk.data.find('stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

# Load SpaCy model
try:
    nlp = spacy.load("en_core_web_md")
except OSError:
    # Download if not available
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_md"])
    nlp = spacy.load("en_core_web_md")

# Initialize HuggingFace summarization pipeline
summarizer_pipeline = None

def initialize_summarizer_pipeline():
    """Initialize the HuggingFace summarization pipeline"""
    global summarizer_pipeline
    try:
        summarizer_pipeline = pipeline("summarization", model="facebook/bart-large-cnn")
    except Exception as e:
        print(f"Error initializing summarization pipeline: {str(e)}")
        # Try a smaller model as fallback
        try:
            summarizer_pipeline = pipeline("summarization", model="sshleifer/distilbart-cnn-6-6")
        except Exception as e:
            print(f"Error initializing fallback summarization pipeline: {str(e)}")

def summarize_huggingface(text, max_length=150, min_length=30):
    """
    Summarize text using HuggingFace transformers
    
    Args:
        text (str): Text to summarize
        max_length (int): Maximum length of the summary in tokens
        min_length (int): Minimum length of the summary in tokens
        
    Returns:
        str: Summarized text
    """
    global summarizer_pipeline
    
    if summarizer_pipeline is None:
        initialize_summarizer_pipeline()
        if summarizer_pipeline is None:
            return None
    
    try:
        # Check if text is too short to summarize
        if len(text.split()) < min_length:
            return text
        
        # Truncate text if it's too long for the model (typically 1024 tokens)
        max_input_length = 1024
        words = text.split()
        if len(words) > max_input_length:
            text = ' '.join(words[:max_input_length])
        
        summary = summarizer_pipeline(text, max_length=max_length, min_length=min_length, do_sample=False)
        return summary[0]['summary_text']
    except Exception as e:
        print(f"Error in HuggingFace summarization: {str(e)}")
        return None

def sentence_similarity(sent1, sent2, stopwords=None):
    """Calculate similarity between two sentences using cosine similarity"""
    if stopwords is None:
        stopwords = []
    
    sent1 = [w.lower() for w in word_tokenize(sent1) if w.lower() not in stopwords]
    sent2 = [w.lower() for w in word_tokenize(sent2) if w.lower() not in stopwords]
    
    all_words = list(set(sent1 + sent2))
    
    vector1 = [0] * len(all_words)
    vector2 = [0] * len(all_words)
    
    # Build the vectors
    for w in sent1:
        if w in all_words:
            vector1[all_words.index(w)] += 1
    
    for w in sent2:
        if w in all_words:
            vector2[all_words.index(w)] += 1
    
    # Calculate cosine similarity
    return 1 - cosine_distance(vector1, vector2)

def build_similarity_matrix(sentences, stop_words):
    """Build similarity matrix for sentences"""
    # Create an empty similarity matrix
    similarity_matrix = np.zeros((len(sentences), len(sentences)))
    
    for i in range(len(sentences)):
        for j in range(len(sentences)):
            if i != j:
                similarity_matrix[i][j] = sentence_similarity(sentences[i], sentences[j], stop_words)
    
    return similarity_matrix

def summarize_extractive(text, num_sentences=3):
    """
    Generate an extractive summary using TextRank algorithm
    
    Args:
        text (str): Text to summarize
        num_sentences (int): Number of sentences in the summary
        
    Returns:
        str: Summarized text
    """
    # Tokenize the text into sentences
    sentences = sent_tokenize(text)
    
    # Check if we have enough sentences to summarize
    if len(sentences) <= num_sentences:
        return text
    
    # Get stop words
    stop_words = set(stopwords.words('english'))
    
    # Build similarity matrix
    similarity_matrix = build_similarity_matrix(sentences, stop_words)
    
    # Apply PageRank algorithm
    nx_graph = nx.from_numpy_array(similarity_matrix)
    scores = nx.pagerank(nx_graph)
    
    # Sort sentences by score and select top ones
    ranked_sentences = sorted(((scores[i], i, s) for i, s in enumerate(sentences)), reverse=True)
    
    # Get the top n sentences based on their position in the original text
    top_sentence_indices = sorted([ranked_sentences[i][1] for i in range(min(num_sentences, len(ranked_sentences)))])
    
    # Combine the selected sentences
    summary = ' '.join([sentences[i] for i in top_sentence_indices])
    
    return summary

def summarize_spacy(text, ratio=0.3):
    """
    Summarize text using SpaCy
    
    Args:
        text (str): Text to summarize
        ratio (float): Proportion of the original text to keep
        
    Returns:
        str: Summarized text
    """
    doc = nlp(text)
    
    # Get sentence scores based on word importance
    sentence_scores = {}
    for sent in doc.sents:
        for token in sent:
            if token.text.lower() not in stopwords.words('english') and token.is_alpha:
                if sent not in sentence_scores:
                    sentence_scores[sent] = token.vector_norm
                else:
                    sentence_scores[sent] += token.vector_norm
    
    # Select top sentences
    select_length = int(len(list(doc.sents)) * ratio)
    if select_length < 1:
        select_length = 1
    
    top_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:select_length]
    top_sentences = [sent[0] for sent in top_sentences]
    
    # Sort sentences by their position in the original text
    top_sentences.sort(key=lambda s: s.start)
    
    # Combine the selected sentences
    summary = ' '.join([sent.text for sent in top_sentences])
    
    return summary

def summarize_text(text, method="extractive", max_length=150, min_length=30, ratio=0.3):
    """
    Summarize text using specified method
    
    Args:
        text (str): Text to summarize
        method (str): Method to use - "extractive", "abstractive", "spacy", or "ensemble"
        max_length (int): Maximum length of the summary in tokens (for abstractive)
        min_length (int): Minimum length of the summary in tokens (for abstractive)
        ratio (float): Proportion of the original text to keep (for extractive)
        
    Returns:
        dict: Summary information including the summary text and method used
    """
    # Check if text is too short to summarize
    if len(text.split()) < min_length:
        return {
            "summary": text,
            "method": "original",
            "original_length": len(text.split()),
            "summary_length": len(text.split())
        }
    
    if method == "extractive":
        # Calculate number of sentences based on ratio
        num_sentences = max(1, int(len(sent_tokenize(text)) * ratio))
        summary = summarize_extractive(text, num_sentences)
        
        return {
            "summary": summary,
            "method": "extractive",
            "original_length": len(text.split()),
            "summary_length": len(summary.split())
        }
    
    elif method == "abstractive":
        summary = summarize_huggingface(text, max_length, min_length)
        
        if summary:
            return {
                "summary": summary,
                "method": "abstractive",
                "original_length": len(text.split()),
                "summary_length": len(summary.split())
            }
        else:
            # Fallback to extractive
            num_sentences = max(1, int(len(sent_tokenize(text)) * ratio))
            summary = summarize_extractive(text, num_sentences)
            
            return {
                "summary": summary,
                "method": "extractive_fallback",
                "original_length": len(text.split()),
                "summary_length": len(summary.split())
            }
    
    elif method == "spacy":
        summary = summarize_spacy(text, ratio)
        
        return {
            "summary": summary,
            "method": "spacy",
            "original_length": len(text.split()),
            "summary_length": len(summary.split())
        }
    
    elif method == "ensemble":
        # Try abstractive first
        abstractive_summary = summarize_huggingface(text, max_length, min_length)
        
        # Get extractive summary
        num_sentences = max(1, int(len(sent_tokenize(text)) * ratio))
        extractive_summary = summarize_extractive(text, num_sentences)
        
        # Get SpaCy summary
        spacy_summary = summarize_spacy(text, ratio)
        
        # Use abstractive if available, otherwise use the better of extractive and spacy
        if abstractive_summary:
            final_summary = abstractive_summary
            method_used = "abstractive"
        else:
            # Choose the summary that retains more of the original meaning
            # Simple heuristic: choose the longer one
            if len(extractive_summary.split()) >= len(spacy_summary.split()):
                final_summary = extractive_summary
                method_used = "extractive"
            else:
                final_summary = spacy_summary
                method_used = "spacy"
        
        return {
            "summary": final_summary,
            "method": method_used,
            "original_length": len(text.split()),
            "summary_length": len(final_summary.split()),
            "all_summaries": {
                "abstractive": abstractive_summary,
                "extractive": extractive_summary,
                "spacy": spacy_summary
            }
        }
    
    # Default to extractive
    num_sentences = max(1, int(len(sent_tokenize(text)) * ratio))
    summary = summarize_extractive(text, num_sentences)
    
    return {
        "summary": summary,
        "method": "extractive_default",
        "original_length": len(text.split()),
        "summary_length": len(summary.split())
    }
