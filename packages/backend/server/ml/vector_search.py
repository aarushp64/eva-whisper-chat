import numpy as np
import faiss
import os
import pickle
import json
from datetime import datetime
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

class VectorSearchEngine:
    """Class for embedding-based search using FAISS"""
    
    def __init__(self, embedding_model="all-MiniLM-L6-v2"):
        self.index = None
        self.documents = []
        self.embeddings = None
        self.embedding_dim = 384  # Default for all-MiniLM-L6-v2
        self.embedding_model_name = embedding_model
        
        # Initialize the embedding model
        try:
            self.embedding_model = SentenceTransformer(f'sentence-transformers/{embedding_model}')
            # Update embedding dimension based on the model
            self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        except Exception as e:
            print(f"Error initializing embedding model: {str(e)}")
            self.embedding_model = None
    
    def add_documents(self, documents, metadata=None):
        """
        Add documents to the search index
        
        Args:
            documents (list): List of document texts
            metadata (list): Optional list of metadata dicts for each document
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.embedding_model is None:
            return False
        
        if metadata is None:
            metadata = [{} for _ in range(len(documents))]
        
        # Ensure metadata list matches documents list
        if len(metadata) != len(documents):
            metadata = metadata[:len(documents)]
            metadata.extend([{} for _ in range(len(documents) - len(metadata))])
        
        # Compute embeddings
        try:
            embeddings = self.embedding_model.encode(documents)
            
            # Initialize index if needed
            if self.index is None:
                self.index = faiss.IndexFlatL2(self.embedding_dim)
            
            # Add embeddings to index
            faiss.normalize_L2(embeddings)
            self.index.add(embeddings)
            
            # Store documents and metadata
            start_idx = len(self.documents)
            for i, (doc, meta) in enumerate(zip(documents, metadata)):
                self.documents.append({
                    "id": start_idx + i,
                    "text": doc,
                    "metadata": meta
                })
            
            return True
        except Exception as e:
            print(f"Error adding documents to index: {str(e)}")
            return False
    
    def search(self, query, k=5):
        """
        Search for documents similar to the query
        
        Args:
            query (str): Query text
            k (int): Number of results to return
            
        Returns:
            list: List of search results with document text, metadata, and similarity score
        """
        if self.embedding_model is None or self.index is None:
            return []
        
        try:
            # Compute query embedding
            query_embedding = self.embedding_model.encode([query])[0]
            query_embedding = query_embedding.reshape(1, -1)
            faiss.normalize_L2(query_embedding)
            
            # Search the index
            distances, indices = self.index.search(query_embedding, min(k, len(self.documents)))
            
            # Format results
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.documents):
                    doc = self.documents[idx]
                    results.append({
                        "id": doc["id"],
                        "text": doc["text"],
                        "metadata": doc["metadata"],
                        "score": float(1.0 - distances[0][i])  # Convert distance to similarity score
                    })
            
            return results
        except Exception as e:
            print(f"Error searching index: {str(e)}")
            return []
    
    def delete_document(self, doc_id):
        """
        Delete a document from the index
        
        Args:
            doc_id (int): Document ID to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        # FAISS doesn't support direct deletion, so we need to rebuild the index
        try:
            # Find the document
            doc_idx = None
            for i, doc in enumerate(self.documents):
                if doc["id"] == doc_id:
                    doc_idx = i
                    break
            
            if doc_idx is None:
                return False
            
            # Remove the document
            self.documents.pop(doc_idx)
            
            # Rebuild the index
            self.rebuild_index()
            
            return True
        except Exception as e:
            print(f"Error deleting document: {str(e)}")
            return False
    
    def rebuild_index(self):
        """
        Rebuild the index from scratch
        
        Returns:
            bool: True if successful, False otherwise
        """
        if self.embedding_model is None:
            return False
        
        try:
            # Extract document texts
            texts = [doc["text"] for doc in self.documents]
            
            # Compute embeddings
            embeddings = self.embedding_model.encode(texts)
            
            # Create a new index
            self.index = faiss.IndexFlatL2(self.embedding_dim)
            
            # Add embeddings to index
            faiss.normalize_L2(embeddings)
            self.index.add(embeddings)
            
            return True
        except Exception as e:
            print(f"Error rebuilding index: {str(e)}")
            return False
    
    def save(self, directory="vector_store"):
        """
        Save the search index and documents to disk
        
        Args:
            directory (str): Directory to save the index to
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(directory, exist_ok=True)
            
            # Save the index
            if self.index is not None:
                faiss.write_index(self.index, f"{directory}/faiss_index.bin")
            
            # Save the documents
            with open(f"{directory}/documents.pkl", "wb") as f:
                pickle.dump(self.documents, f)
            
            # Save metadata
            metadata = {
                "embedding_model": self.embedding_model_name,
                "embedding_dim": self.embedding_dim,
                "document_count": len(self.documents),
                "timestamp": datetime.now().isoformat()
            }
            
            with open(f"{directory}/metadata.json", "w") as f:
                json.dump(metadata, f)
            
            return True
        except Exception as e:
            print(f"Error saving index: {str(e)}")
            return False
    
    @classmethod
    def load(cls, directory="vector_store"):
        """
        Load a search index and documents from disk
        
        Args:
            directory (str): Directory to load the index from
            
        Returns:
            VectorSearchEngine: Loaded search engine
        """
        try:
            # Check if files exist
            if not os.path.exists(f"{directory}/metadata.json"):
                return cls()
            
            # Load metadata
            with open(f"{directory}/metadata.json", "r") as f:
                metadata = json.load(f)
            
            # Create a new instance with the same embedding model
            engine = cls(embedding_model=metadata.get("embedding_model", "all-MiniLM-L6-v2"))
            
            # Load documents
            if os.path.exists(f"{directory}/documents.pkl"):
                with open(f"{directory}/documents.pkl", "rb") as f:
                    engine.documents = pickle.load(f)
            
            # Load index
            if os.path.exists(f"{directory}/faiss_index.bin"):
                engine.index = faiss.read_index(f"{directory}/faiss_index.bin")
            
            return engine
        except Exception as e:
            print(f"Error loading index: {str(e)}")
            return cls()


class ChromaSearchEngine:
    """Class for embedding-based search using ChromaDB"""
    
    def __init__(self, collection_name="eva_documents", embedding_model="all-MiniLM-L6-v2"):
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model
        
        # Initialize ChromaDB client
        try:
            self.client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory="chroma_db"
            ))
            
            # Set up embedding function
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=f"sentence-transformers/{embedding_model}"
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
        except Exception as e:
            print(f"Error initializing ChromaDB: {str(e)}")
            self.client = None
            self.collection = None
    
    def add_documents(self, documents, metadata=None, ids=None):
        """
        Add documents to the search index
        
        Args:
            documents (list): List of document texts
            metadata (list): Optional list of metadata dicts for each document
            ids (list): Optional list of IDs for each document
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.collection is None:
            return False
        
        try:
            # Generate IDs if not provided
            if ids is None:
                ids = [f"doc_{i}_{datetime.now().timestamp()}" for i in range(len(documents))]
            
            # Ensure IDs list matches documents list
            if len(ids) != len(documents):
                ids = ids[:len(documents)]
                ids.extend([f"doc_{i+len(ids)}_{datetime.now().timestamp()}" for i in range(len(documents) - len(ids))])
            
            # Generate metadata if not provided
            if metadata is None:
                metadata = [{} for _ in range(len(documents))]
            
            # Ensure metadata list matches documents list
            if len(metadata) != len(documents):
                metadata = metadata[:len(documents)]
                metadata.extend([{} for _ in range(len(documents) - len(metadata))])
            
            # Add documents to collection
            self.collection.add(
                documents=documents,
                metadatas=metadata,
                ids=ids
            )
            
            return True
        except Exception as e:
            print(f"Error adding documents to ChromaDB: {str(e)}")
            return False
    
    def search(self, query, k=5, filter_metadata=None):
        """
        Search for documents similar to the query
        
        Args:
            query (str): Query text
            k (int): Number of results to return
            filter_metadata (dict): Optional metadata filter
            
        Returns:
            list: List of search results with document text, metadata, and similarity score
        """
        if self.collection is None:
            return []
        
        try:
            # Search the collection
            results = self.collection.query(
                query_texts=[query],
                n_results=k,
                where=filter_metadata
            )
            
            # Format results
            formatted_results = []
            
            if results and 'documents' in results and results['documents']:
                documents = results['documents'][0]
                metadatas = results['metadatas'][0] if 'metadatas' in results and results['metadatas'] else [{}] * len(documents)
                ids = results['ids'][0] if 'ids' in results and results['ids'] else [f"unknown_{i}" for i in range(len(documents))]
                distances = results['distances'][0] if 'distances' in results and results['distances'] else [0] * len(documents)
                
                for i, (doc, meta, doc_id, distance) in enumerate(zip(documents, metadatas, ids, distances)):
                    # Convert distance to similarity score (ChromaDB returns distances, lower is better)
                    similarity = 1.0 - min(distance, 1.0)
                    
                    formatted_results.append({
                        "id": doc_id,
                        "text": doc,
                        "metadata": meta,
                        "score": float(similarity)
                    })
            
            return formatted_results
        except Exception as e:
            print(f"Error searching ChromaDB: {str(e)}")
            return []
    
    def delete_document(self, doc_id):
        """
        Delete a document from the index
        
        Args:
            doc_id (str): Document ID to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.collection is None:
            return False
        
        try:
            # Delete the document
            self.collection.delete(ids=[doc_id])
            return True
        except Exception as e:
            print(f"Error deleting document from ChromaDB: {str(e)}")
            return False
    
    def get_document(self, doc_id):
        """
        Get a document by ID
        
        Args:
            doc_id (str): Document ID
            
        Returns:
            dict: Document information
        """
        if self.collection is None:
            return None
        
        try:
            # Get the document
            result = self.collection.get(ids=[doc_id])
            
            if result and 'documents' in result and result['documents']:
                document = result['documents'][0]
                metadata = result['metadatas'][0] if 'metadatas' in result and result['metadatas'] else {}
                
                return {
                    "id": doc_id,
                    "text": document,
                    "metadata": metadata
                }
            
            return None
        except Exception as e:
            print(f"Error getting document from ChromaDB: {str(e)}")
            return None
    
    def list_documents(self, limit=100, offset=0, filter_metadata=None):
        """
        List documents in the collection
        
        Args:
            limit (int): Maximum number of documents to return
            offset (int): Offset for pagination
            filter_metadata (dict): Optional metadata filter
            
        Returns:
            list: List of documents
        """
        if self.collection is None:
            return []
        
        try:
            # Get documents
            result = self.collection.get(
                limit=limit,
                offset=offset,
                where=filter_metadata
            )
            
            # Format results
            documents = []
            
            if result and 'documents' in result and result['documents']:
                for i, doc in enumerate(result['documents']):
                    doc_id = result['ids'][i] if 'ids' in result and result['ids'] else f"unknown_{i}"
                    metadata = result['metadatas'][i] if 'metadatas' in result and result['metadatas'] else {}
                    
                    documents.append({
                        "id": doc_id,
                        "text": doc,
                        "metadata": metadata
                    })
            
            return documents
        except Exception as e:
            print(f"Error listing documents from ChromaDB: {str(e)}")
            return []
    
    def save(self):
        """
        Save the ChromaDB collection to disk
        
        Returns:
            bool: True if successful, False otherwise
        """
        if self.client is None:
            return False
        
        try:
            # Persist the client
            self.client.persist()
            return True
        except Exception as e:
            print(f"Error saving ChromaDB: {str(e)}")
            return False
