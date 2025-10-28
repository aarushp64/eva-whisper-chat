"""
RAG Engine - Combines retrieval and generation for context-aware responses.
"""

from typing import List, Dict, Any, Optional
from loguru import logger

from .vector_store import VectorStore
from ..llm.base_llm import BaseLLM, Message


class RAGEngine:
    """
    Retrieval Augmented Generation Engine.
    
    Combines semantic search with LLM generation to provide
    context-aware responses based on stored knowledge.
    """
    
    def __init__(
        self,
        llm: BaseLLM,
        vector_store: VectorStore,
        max_context_docs: int = 5,
        similarity_threshold: float = 0.7
    ):
        """
        Initialize RAG Engine.
        
        Args:
            llm: Language model instance
            vector_store: Vector store for retrieval
            max_context_docs: Maximum number of documents to retrieve
            similarity_threshold: Minimum similarity score for relevance
        """
        self.llm = llm
        self.vector_store = vector_store
        self.max_context_docs = max_context_docs
        self.similarity_threshold = similarity_threshold
        
        logger.info("RAG Engine initialized")
    
    def retrieve_context(
        self,
        query: str,
        n_results: Optional[int] = None,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context documents for a query.
        
        Args:
            query: User query
            n_results: Number of results (defaults to max_context_docs)
            metadata_filter: Optional metadata filter
            
        Returns:
            List of relevant documents with metadata
        """
        n_results = n_results or self.max_context_docs
        
        try:
            results = self.vector_store.search(
                query=query,
                n_results=n_results,
                where=metadata_filter
            )
            
            # Filter by similarity threshold
            relevant_docs = []
            for i, distance in enumerate(results['distances']):
                # ChromaDB uses distance (lower is better), convert to similarity
                similarity = 1 - distance
                
                if similarity >= self.similarity_threshold:
                    relevant_docs.append({
                        'content': results['documents'][i],
                        'metadata': results['metadatas'][i],
                        'similarity': similarity,
                        'id': results['ids'][i]
                    })
            
            logger.info(f"Retrieved {len(relevant_docs)} relevant documents for query")
            return relevant_docs
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return []
    
    def generate_with_context(
        self,
        query: str,
        conversation_history: Optional[List[Message]] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a response using retrieved context.
        
        Args:
            query: User query
            conversation_history: Previous conversation messages
            system_prompt: Optional system prompt
            temperature: LLM temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dictionary with response and context used
        """
        try:
            # Retrieve relevant context
            context_docs = self.retrieve_context(query)
            
            # Build context string
            context_str = self._format_context(context_docs)
            
            # Build messages
            messages = []
            
            # Add system prompt
            if system_prompt:
                system_message = system_prompt
            else:
                system_message = "You are Eva, an intelligent AI assistant."
            
            if context_str:
                system_message += f"\n\nRelevant context from memory:\n{context_str}"
            
            messages.append(Message(role="system", content=system_message))
            
            # Add conversation history
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add current query
            messages.append(Message(role="user", content=query))
            
            # Generate response
            response = self.llm.generate(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return {
                'response': response.content,
                'context_used': context_docs,
                'model': response.model,
                'tokens_used': response.tokens_used
            }
            
        except Exception as e:
            logger.error(f"Error generating with context: {e}")
            raise
    
    async def generate_with_context_stream(
        self,
        query: str,
        conversation_history: Optional[List[Message]] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ):
        """
        Generate a streaming response using retrieved context.
        
        Args:
            query: User query
            conversation_history: Previous conversation messages
            system_prompt: Optional system prompt
            temperature: LLM temperature
            max_tokens: Maximum tokens to generate
            
        Yields:
            Chunks of generated text
        """
        try:
            # Retrieve relevant context
            context_docs = self.retrieve_context(query)
            
            # Build context string
            context_str = self._format_context(context_docs)
            
            # Build messages
            messages = []
            
            # Add system prompt
            if system_prompt:
                system_message = system_prompt
            else:
                system_message = "You are Eva, an intelligent AI assistant."
            
            if context_str:
                system_message += f"\n\nRelevant context from memory:\n{context_str}"
            
            messages.append(Message(role="system", content=system_message))
            
            # Add conversation history
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add current query
            messages.append(Message(role="user", content=query))
            
            # Generate streaming response
            async for chunk in self.llm.generate_stream(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            ):
                yield chunk
                
        except Exception as e:
            logger.error(f"Error in streaming generation with context: {e}")
            raise
    
    def _format_context(self, context_docs: List[Dict[str, Any]]) -> str:
        """
        Format context documents into a string.
        
        Args:
            context_docs: List of context documents
            
        Returns:
            Formatted context string
        """
        if not context_docs:
            return ""
        
        formatted = []
        for i, doc in enumerate(context_docs, 1):
            metadata = doc.get('metadata', {})
            timestamp = metadata.get('timestamp', 'Unknown time')
            source = metadata.get('source', 'Unknown source')
            
            formatted.append(
                f"[{i}] ({timestamp} - {source})\n{doc['content']}"
            )
        
        return "\n\n".join(formatted)
    
    def add_to_memory(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add content to the vector store memory.
        
        Args:
            content: Text content to store
            metadata: Optional metadata
            
        Returns:
            Document ID
        """
        try:
            import uuid
            doc_id = str(uuid.uuid4())
            
            self.vector_store.add_documents(
                documents=[content],
                metadatas=[metadata] if metadata else None,
                ids=[doc_id]
            )
            
            logger.info(f"Added content to memory: {doc_id}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Error adding to memory: {e}")
            raise
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the memory store.
        
        Returns:
            Dictionary with memory statistics
        """
        return self.vector_store.get_collection_stats()
