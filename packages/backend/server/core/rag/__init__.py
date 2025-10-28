"""
RAG (Retrieval Augmented Generation) System

Provides semantic search and context retrieval using:
- ChromaDB for vector storage
- Sentence Transformers for embeddings
- Conversation history and knowledge base integration
"""

from .vector_store import VectorStore
from .rag_engine import RAGEngine

__all__ = ['VectorStore', 'RAGEngine']
