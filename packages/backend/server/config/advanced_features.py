"""
Advanced Features Configuration for EVA

This module contains configuration settings for all advanced features in EVA.
Enable or disable features as needed and configure their parameters.
"""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
CACHE_DIR = BASE_DIR / "cache"
UPLOADS_DIR = BASE_DIR / "uploads"
EXPORTS_DIR = BASE_DIR / "exports"

# Create directories if they don't exist
for directory in [DATA_DIR, MODELS_DIR, CACHE_DIR, UPLOADS_DIR, EXPORTS_DIR]:
    directory.mkdir(exist_ok=True)

# Feature flags - enable or disable features
FEATURES = {
    # Core capabilities
    "advanced_nlp": True,
    "advanced_ml": True,
    "voice_processing": True,
    "data_analysis": True,
    "web_integration": True,
    
    # Advanced capabilities
    "multimodal": True,  # Image, document processing
    "rag": True,  # Retrieval Augmented Generation
    "multi_agent": True,  # Multiple specialized agents
    "streaming": True,  # Streaming responses
    "caching": True,  # Response and computation caching
    "background_tasks": True,  # Asynchronous processing
    "scheduled_tasks": True,  # Scheduled operations
    "privacy_preserving": True,  # Enhanced privacy features
    "monitoring": True,  # System monitoring
    "distributed_processing": False,  # Distributed computation (advanced)
}

# NLP Configuration
NLP_CONFIG = {
    "intent_recognition": {
        "enabled": True,
        "default_method": "ensemble",  # spacy, huggingface, rasa, ensemble
        "confidence_threshold": 0.65,
        "context_aware": True,
        "multi_intent": True,
    },
    "entity_recognition": {
        "enabled": True,
        "default_method": "ensemble",  # spacy, huggingface, regex, ensemble
        "confidence_threshold": 0.6,
        "custom_entities": True,
        "contextual": True,  # Enable contextual entity resolution
        "hierarchical": True,  # Enable hierarchical entity recognition
        "relationship_extraction": True,  # Extract relationships between entities
        "knowledge_base_linking": True,  # Link entities to knowledge bases
        "anonymization": {
            "enabled": True,  # Enable sensitive entity anonymization
            "sensitive_types": ["PERSON", "EMAIL", "PHONE_NUMBER", "CREDIT_CARD", "SSN", "ADDRESS"]
        },
        "custom_entity_types": {
            "enabled": True,
            "types": ["EMAIL", "PHONE_NUMBER", "URL", "IP_ADDRESS", "CREDIT_CARD", "SSN", 
                     "USERNAME", "HASHTAG", "CURRENCY_AMOUNT", "PERCENTAGE", "MEASUREMENT", 
                     "TIME", "DATE_MDY", "DATE_DMY", "DATE_YMD", "FILE_PATH", "VERSION_NUMBER", "ISBN"]
        },
    },
    "sentiment_analysis": {
        "enabled": True,
        "default_method": "ensemble",  # vader, textblob, huggingface, ensemble
        "emotion_detection": True,
    },
    "text_summarization": {
        "enabled": True,
        "default_method": "extractive",  # extractive, abstractive, hybrid
        "max_length": 200,
    },
    "question_answering": {
        "enabled": True,
        "default_method": "rag",  # huggingface, langchain, openai, rag
        "use_web_search": True,
    },
    "language_translation": {
        "enabled": True,
        "default_model": "helsinki-nlp",  # helsinki-nlp, google, openai
        "auto_detect": True,
    },
}

# Data Analytics Configuration
DATA_ANALYTICS_CONFIG = {
    "enabled": True,
    "data_processing": {
        "enabled": True,
        "cleaning": True,
        "normalization": True,
        "outlier_detection": True,
        "missing_value_handling": "mean"  # mean, median, mode, value
    },
    "statistical_analysis": {
        "enabled": True,
        "descriptive_stats": True,
        "correlation_analysis": True,
        "hypothesis_testing": True
    },
    "time_series_analysis": {
        "enabled": True,
        "forecasting": True,
        "seasonality_detection": True,
        "trend_analysis": True,
        "anomaly_detection": True,
        "default_model": "arima"  # arima, prophet, exponential_smoothing
    },
    "visualization": {
        "enabled": True,
        "chart_types": ["line", "bar", "scatter", "pie", "heatmap"],
        "default_type": "line",
        "color_scheme": "viridis",
        "interactive": True
    },
    "insight_extraction": {
        "enabled": True,
        "threshold": 0.7,  # Minimum confidence for insights
        "max_insights": 5,  # Maximum number of insights to extract
        "categories": ["trend", "anomaly", "correlation", "pattern", "comparison"]
    },
    "export_formats": ["json", "csv", "excel", "image"]
}

# User Personalization Configuration
USER_PERSONALIZATION_CONFIG = {
    "enabled": True,
    "update_frequency": "message",  # message, session, daily, none
    "features": ["sentiment", "topics", "style", "preferences", "behavior"],
    "communication_style": {
        "enabled": True,
        "default": "balanced",
        "adaptation_rate": 0.7  # How quickly to adapt to user preferences (0-1)
    },
    "topic_tracking": {
        "enabled": True,
        "max_topics": 10,  # Maximum number of favorite topics to track
        "recency_weight": 0.6  # Weight for recent topics vs. frequent topics
    },
    "behavior_analysis": {
        "enabled": True,
        "patterns": ["time_of_day", "session_length", "query_complexity", "response_engagement"],
        "lookback_days": 30  # Days of history to analyze
    },
    "preference_learning": {
        "enabled": True,
        "explicit_weight": 0.8,  # Weight for explicitly stated preferences
        "implicit_weight": 0.2,  # Weight for inferred preferences
        "categories": ["communication_style", "response_length", "formality", "topics", "features"]
    },
    "profile_storage": {
        "enabled": True,
        "storage_type": "db",  # db, file, redis
        "encryption": True,
        "user_accessible": True  # Whether users can view/edit their profile
    }
}

# Machine Learning Configuration
ML_CONFIG = {
    "enabled": True,
    "model_management": {
        "enabled": True,
        "storage_path": "data/models",
        "versioning": True,
        "metadata_tracking": True,
        "auto_update": True
    },
    "classification": {
        "enabled": True,
        "default_model": "random_forest",  # random_forest, logistic_regression, svm, knn
        "evaluation_metric": "f1",  # accuracy, precision, recall, f1
        "cross_validation": True,
        "hyperparameter_tuning": True
    },
    "regression": {
        "enabled": True,
        "default_model": "random_forest",  # random_forest, linear_regression, svr, knn
        "evaluation_metric": "r2",  # mse, mae, r2
        "cross_validation": True,
        "hyperparameter_tuning": True
    },
    "clustering": {
        "enabled": True,
        "default_method": "kmeans",  # kmeans, dbscan, hierarchical
        "auto_determine_clusters": True,
        "evaluation_metric": "silhouette",  # silhouette, davies_bouldin, calinski_harabasz
    },
    "anomaly_detection": {
        "enabled": True,
        "default_method": "isolation_forest",  # isolation_forest, lof, ocsvm
        "contamination": 0.05,  # Expected proportion of outliers
    },
    "vector_search": {
        "enabled": True,
        "default_engine": "faiss",  # faiss, chroma, pinecone, pgvector
        "embedding_model": "sentence-transformers/all-mpnet-base-v2",
        "dimensions": 768,
        "distance_metric": "cosine",  # cosine, l2, dot
    },
    "recommendation": {
        "enabled": True,
        "methods": ["collaborative", "content-based", "hybrid"],
        "cold_start_strategy": "content-based",
    },
}

# Speech Processing Configuration
SPEECH_CONFIG = {
    "speech_to_text": {
        "enabled": True,
        "default_model": "whisper",  # whisper, faster-whisper, deepspeech, vosk
        "whisper_model": "base",  # tiny, base, small, medium, large
        "language_detection": True,
        "speaker_diarization": True,
        "noise_reduction": True,
        "streaming": True,
    },
    "text_to_speech": {
        "enabled": True,
        "default_provider": "elevenlabs",  # elevenlabs, openai, google, local
        "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Default ElevenLabs voice
        "emotion_aware": True,
        "streaming": True,
    },
    "voice_analysis": {
        "enabled": True,
        "emotion_detection": True,
        "stress_detection": True,
        "identity_verification": False,
    },
}

# Memory Configuration
MEMORY_CONFIG = {
    "hierarchical_memory": {
        "enabled": True,
        "short_term": {
            "enabled": True,
            "capacity": 20,  # Number of recent items to keep in short-term memory
            "recency_weight": 0.8,  # Weight for recency in importance calculation
            "access_boost": 0.1  # Importance boost per access
        },
        "medium_term": {
            "enabled": True,
            "capacity": 100,  # Items to keep in medium-term memory
            "importance_threshold": 0.5,  # Minimum importance to retain
            "summarization": True  # Whether to summarize medium-term memories
        },
        "long_term": {
            "enabled": True,
            "capacity": 1000,  # Maximum items in long-term memory
            "importance_threshold": 0.7,  # Minimum importance to transfer to long-term
            "consolidation_interval": 24,  # Hours between memory consolidation
            "categories": ["conversation", "user_preference", "entity", "fact"]
        },
        "semantic_memory": {
            "enabled": True,
            "storage_engine": "faiss",  # faiss, chroma, pinecone, pgvector
            "embedding_model": "sentence-transformers/all-mpnet-base-v2",
            "dimensions": 768,
            "similarity_threshold": 0.7  # Minimum similarity for retrieval
        }
    },
    "conversation_memory": {
        "enabled": True,
        "storage_type": "hybrid",  # db, vector, file, redis, hybrid
        "max_history": 100,  # Maximum messages to keep in active memory
        "ttl": 30,  # Days to keep memories before archiving
    },
    "episodic_memory": {
        "enabled": True,
        "summarization": True,
        "key_extraction": True,
    },
    "long_term_memory": {
        "enabled": True,
        "storage_type": "vector",  # db, vector, file
        "refresh_strategy": "access_based",  # time_based, access_based, importance_based
    },
}

# Data Analysis Configuration
DATA_ANALYSIS_CONFIG = {
    "data_processing": {
        "enabled": True,
        "supported_formats": ["csv", "excel", "json", "parquet", "sql"],
        "max_file_size_mb": 50,
        "auto_clean": True,
    },
    "visualization": {
        "enabled": True,
        "default_library": "plotly",  # matplotlib, seaborn, plotly
        "interactive": True,
    },
    "natural_language_querying": {
        "enabled": True,
        "sql_generation": True,
        "query_validation": True,
    },
    "insights_generation": {
        "enabled": True,
        "statistical_analysis": True,
        "anomaly_detection": True,
        "correlation_analysis": True,
    },
}

# Web Integration Configuration
WEB_CONFIG = {
    "web_search": {
        "enabled": True,
        "default_engine": "serpapi",  # serpapi, google, bing, brave
        "fallback_to_scraping": True,
        "max_results": 5,
        "cache_ttl": 3600,  # seconds
    },
    "content_extraction": {
        "enabled": True,
        "article_extraction": True,
        "metadata_extraction": True,
        "main_image_extraction": True,
    },
    "fact_checking": {
        "enabled": True,
        "sources_required": 2,
        "confidence_threshold": 0.7,
    },
}

# Multimodal Configuration
MULTIMODAL_CONFIG = {
    "image_processing": {
        "enabled": True,
        "analysis_model": "clip",  # clip, resnet, efficientnet
        "captioning": True,
        "object_detection": True,
        "face_detection": True,
    },
    "document_processing": {
        "enabled": True,
        "supported_formats": ["pdf", "docx", "pptx", "txt", "md"],
        "extract_tables": True,
        "extract_images": True,
    },
    "chart_recognition": {
        "enabled": True,
        "data_extraction": True,
        "chart_type_detection": True,
    },
}

# RAG (Retrieval Augmented Generation) Configuration
RAG_CONFIG = {
    "enabled": True,
    "retrieval_method": "hybrid",  # semantic, keyword, hybrid
    "sources": ["knowledge_base", "conversation_history", "web", "documents"],
    "max_chunks": 10,
    "reranking": True,
    "citation": True,
}

# Database Configuration
DATABASE_CONFIG = {
    "enabled": True,
    "default_type": "sqlite",  # sqlite, postgres, mysql
    "connection_pooling": True,
    "max_connections": 10,
    "timeout": 30,  # Connection timeout in seconds
    "sqlite": {
        "enabled": True,
        "db_path": "data/db/eva.db",
        "journal_mode": "WAL",  # Write-Ahead Logging for better concurrency
        "synchronous": "NORMAL",  # Balance between safety and performance
    },
    "postgres": {
        "enabled": False,
        "host": "localhost",
        "port": 5432,
        "database": "eva",
        "user": "eva_user",
        "password_env": "POSTGRES_PASSWORD",
        "ssl": False,
    },
    "mysql": {
        "enabled": False,
        "host": "localhost",
        "port": 3306,
        "database": "eva",
        "user": "eva_user",
        "password_env": "MYSQL_PASSWORD",
        "ssl": False,
    },
    "vector_db": {
        "enabled": True,
        "type": "faiss",  # faiss, chroma, pinecone, pgvector
        "dimensions": 768,
        "metric": "cosine",  # cosine, l2, dot
        "index_type": "IVF100,PQ16",  # For FAISS
        "api_key_env": "PINECONE_API_KEY",  # For Pinecone
    },
    "document_db": {
        "enabled": False,
        "type": "mongodb",  # mongodb
        "uri_env": "MONGODB_URI",
        "database": "eva",
    },
    "key_value_store": {
        "enabled": False,
        "type": "redis",  # redis
        "host": "localhost",
        "port": 6379,
        "password_env": "REDIS_PASSWORD",
        "db": 0,
    },
    "orm": {
        "enabled": True,
        "type": "sqlalchemy",  # sqlalchemy
        "echo": False,  # Log SQL queries
        "pool_size": 5,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 3600,  # Recycle connections after 1 hour
    },
}

# Security Configuration
SECURITY_CONFIG = {
    "encryption": {
        "enabled": True,
        "method": "AES-256",
        "key_rotation": True,
    },
    "data_privacy": {
        "enabled": True,
        "pii_detection": True,
        "pii_redaction": True,
        "data_minimization": True,
    },
    "rate_limiting": {
        "enabled": True,
        "max_requests_per_minute": 60,
        "max_tokens_per_day": 100000,
    },
    "audit_logging": {
        "enabled": True,
        "log_level": "INFO",
        "sensitive_operations": True,
    },
}

# Response Generator Configuration
RESPONSE_CONFIG = {
    "enabled": True,
    "memory_integration": True,  # Integrate with memory system
    "contextual_awareness": True,  # Use context for responses
    "personalization": True,  # Personalize responses based on user profile
    "multimodal": {
        "enabled": True,
        "text": True,
        "images": True,
        "charts": True,
        "audio": True
    },
    "communication_styles": {
        "enabled": True,
        "styles": {
            "empathetic": {
                "description": "Focus on understanding and validating emotions",
                "default": True
            },
            "informative": {
                "description": "Focus on providing clear, accurate information",
                "default": False
            },
            "concise": {
                "description": "Be brief and to the point",
                "default": False
            },
            "friendly": {
                "description": "Warm, conversational, and approachable",
                "default": False
            },
            "professional": {
                "description": "Maintain a professional, respectful tone",
                "default": False
            }
        }
    },
    "response_length": {
        "enabled": True,
        "options": ["short", "medium", "long"],
        "default": "medium"
    },
    "formality": {
        "enabled": True,
        "options": ["formal", "casual", "neutral"],
        "default": "casual"
    },
    "fallback_responses": {
        "enabled": True,
        "categories": ["positive", "negative", "neutral", "greeting", "farewell", "confusion", "clarification"]
    }
}

# LLM Configuration
LLM_CONFIG = {
    "default_provider": "openai",  # openai, anthropic, google, cohere, local
    "providers": {
        "openai": {
            "enabled": True,
            "model": "gpt-3.5-turbo",
            "api_key_env": "OPENAI_API_KEY",
            "streaming": True,
        },
        "anthropic": {
            "enabled": True,
            "model": "claude-2",
            "api_key_env": "ANTHROPIC_API_KEY",
            "streaming": True,
        },
        "google": {
            "enabled": True,
            "model": "gemini-pro",
            "api_key_env": "GOOGLE_API_KEY",
            "streaming": True,
        },
        "cohere": {
            "enabled": True,
            "model": "command",
            "api_key_env": "COHERE_API_KEY",
            "streaming": False,
        },
        "local": {
            "enabled": False,
            "model_path": str(MODELS_DIR / "llama-2-7b-chat.gguf"),
            "context_length": 4096,
            "streaming": True,
        },
    },
    "fallback_strategy": "waterfall",  # waterfall, round-robin, fastest
    "caching": True,
    "cache_ttl": 3600,  # seconds
}

# Get feature status
def is_feature_enabled(feature_name):
    """Check if a feature is enabled"""
    return FEATURES.get(feature_name, False)

# Get configuration for a specific module
def get_module_config(module_name):
    """Get configuration for a specific module"""
    config_map = {
        "nlp": NLP_CONFIG,
        "ml": ML_CONFIG,
        "speech": SPEECH_CONFIG,
        "memory": MEMORY_CONFIG,
        "data_analysis": DATA_ANALYSIS_CONFIG,
        "web": WEB_CONFIG,
        "multimodal": MULTIMODAL_CONFIG,
        "rag": RAG_CONFIG,
        "security": SECURITY_CONFIG,
        "llm": LLM_CONFIG,
    }
    return config_map.get(module_name, {})
