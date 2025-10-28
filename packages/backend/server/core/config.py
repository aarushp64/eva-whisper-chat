"""
Configuration for the AI Agent system.
"""

import os
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class LLMConfig:
    """Configuration for LLM."""
    provider: str = "ollama"  # ollama, openai, anthropic
    model_name: str = "llama3.2"
    host: str = "http://localhost:11434"
    temperature: float = 0.7
    max_tokens: int = 2000


@dataclass
class RAGConfig:
    """Configuration for RAG system."""
    collection_name: str = "eva_memory"
    persist_directory: str = "./data/vector_store"
    embedding_model: str = "all-MiniLM-L6-v2"
    max_context_docs: int = 5
    similarity_threshold: float = 0.7


@dataclass
class AgentConfig:
    """Configuration for Agent."""
    max_iterations: int = 5
    enable_tools: bool = True
    enable_memory: bool = True
    enable_learning: bool = True


@dataclass
class WhisperConfig:
    """Configuration for Whisper speech-to-text."""
    model_size: str = "base"  # tiny, base, small, medium, large
    language: str = "en"
    device: str = "cpu"  # cpu or cuda


class Config:
    """Main configuration class."""
    
    def __init__(self):
        self.llm = LLMConfig(
            provider=os.getenv("LLM_PROVIDER", "ollama"),
            model_name=os.getenv("LLM_MODEL", "llama3.2"),
            host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2000"))
        )
        
        self.rag = RAGConfig(
            collection_name=os.getenv("RAG_COLLECTION", "eva_memory"),
            persist_directory=os.getenv("RAG_PERSIST_DIR", "./data/vector_store"),
            embedding_model=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
            max_context_docs=int(os.getenv("RAG_MAX_DOCS", "5")),
            similarity_threshold=float(os.getenv("RAG_SIMILARITY", "0.7"))
        )
        
        self.agent = AgentConfig(
            max_iterations=int(os.getenv("AGENT_MAX_ITERATIONS", "5")),
            enable_tools=os.getenv("AGENT_ENABLE_TOOLS", "true").lower() == "true",
            enable_memory=os.getenv("AGENT_ENABLE_MEMORY", "true").lower() == "true",
            enable_learning=os.getenv("AGENT_ENABLE_LEARNING", "true").lower() == "true"
        )
        
        self.whisper = WhisperConfig(
            model_size=os.getenv("WHISPER_MODEL", "base"),
            language=os.getenv("WHISPER_LANGUAGE", "en"),
            device=os.getenv("WHISPER_DEVICE", "cpu")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'llm': {
                'provider': self.llm.provider,
                'model_name': self.llm.model_name,
                'host': self.llm.host,
                'temperature': self.llm.temperature,
                'max_tokens': self.llm.max_tokens
            },
            'rag': {
                'collection_name': self.rag.collection_name,
                'persist_directory': self.rag.persist_directory,
                'embedding_model': self.rag.embedding_model,
                'max_context_docs': self.rag.max_context_docs,
                'similarity_threshold': self.rag.similarity_threshold
            },
            'agent': {
                'max_iterations': self.agent.max_iterations,
                'enable_tools': self.agent.enable_tools,
                'enable_memory': self.agent.enable_memory,
                'enable_learning': self.agent.enable_learning
            },
            'whisper': {
                'model_size': self.whisper.model_size,
                'language': self.whisper.language,
                'device': self.whisper.device
            }
        }


# Global config instance
config = Config()
