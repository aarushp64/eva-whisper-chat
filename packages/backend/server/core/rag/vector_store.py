"""
Vector Store using ChromaDB for semantic search and retrieval.
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from loguru import logger
import os


class VectorStore:
    """Manages vector embeddings and semantic search using ChromaDB."""
    
    def __init__(
        self,
        collection_name: str = "eva_memory",
        persist_directory: str = "./data/vector_store",
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize Vector Store.
        
        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory to persist the database
            embedding_model: Sentence transformer model name
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        # Create persist directory if it doesn't exist
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Eva conversation memory and knowledge base"}
        )
        
        logger.info(f"Vector store initialized with collection: {collection_name}")
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> None:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of text documents
            metadatas: Optional metadata for each document
            ids: Optional IDs for each document (auto-generated if not provided)
        """
        try:
            # Generate embeddings
            embeddings = self.embedding_model.encode(documents).tolist()
            
            # Generate IDs if not provided
            if ids is None:
                import uuid
                ids = [str(uuid.uuid4()) for _ in documents]
            
            # Add to collection
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(documents)} documents to vector store")
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search for similar documents using semantic search.
        
        Args:
            query: Search query text
            n_results: Number of results to return
            where: Optional metadata filter
            
        Returns:
            Dictionary containing documents, distances, and metadata
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])[0].tolist()
            
            # Search in collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where
            )
            
            return {
                'documents': results['documents'][0] if results['documents'] else [],
                'distances': results['distances'][0] if results['distances'] else [],
                'metadatas': results['metadatas'][0] if results['metadatas'] else [],
                'ids': results['ids'][0] if results['ids'] else []
            }
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            raise
    
    def delete_documents(self, ids: List[str]) -> None:
        """
        Delete documents from the vector store.
        
        Args:
            ids: List of document IDs to delete
        """
        try:
            self.collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents from vector store")
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            raise
    
    def update_document(
        self,
        id: str,
        document: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update a document in the vector store.
        
        Args:
            id: Document ID
            document: New document text
            metadata: Optional new metadata
        """
        try:
            # Generate new embedding
            embedding = self.embedding_model.encode([document])[0].tolist()
            
            # Update in collection
            self.collection.update(
                ids=[id],
                documents=[document],
                embeddings=[embedding],
                metadatas=[metadata] if metadata else None
            )
            
            logger.info(f"Updated document {id}")
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection.
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            count = self.collection.count()
            return {
                'name': self.collection_name,
                'count': count,
                'persist_directory': self.persist_directory
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}
    
    def clear_collection(self) -> None:
        """Clear all documents from the collection."""
        try:
            # Delete the collection and recreate it
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Eva conversation memory and knowledge base"}
            )
            logger.info(f"Cleared collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            raise
