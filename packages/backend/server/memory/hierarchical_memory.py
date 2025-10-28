"""
Hierarchical Memory System

This module implements a hierarchical memory system with:
1. Short-term memory (recent conversations)
2. Medium-term memory (current session)
3. Long-term memory (persistent user information)
4. Semantic memory (vector-based retrieval)
5. Episodic memory (time-based events)
"""

import os
import json
import time
import pickle
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path
import numpy as np
# FAISS and SentenceTransformer are optional heavy dependencies. Import them
# lazily and fall back gracefully if they're not installed so the backend can
# run in a lightweight/demo mode.
try:
    import faiss
except Exception:
    faiss = None

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None

# Import from base conversation memory
from memory.conversation_memory import ConversationMemory

# Import advanced features configuration
sys_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if sys_path not in os.sys.path:
    os.sys.path.append(sys_path)

from config.advanced_features import MEMORY_CONFIG, is_feature_enabled

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Memory configuration
memory_config = MEMORY_CONFIG.get("conversation_memory", {})
MAX_HISTORY = memory_config.get("max_history", 100)
TTL_DAYS = memory_config.get("ttl", 30)
STORAGE_TYPE = memory_config.get("storage_type", "hybrid")

# Semantic memory configuration
semantic_config = MEMORY_CONFIG.get("semantic_memory", {})
EMBEDDING_MODEL = semantic_config.get("embedding_model", "sentence-transformers/all-mpnet-base-v2")
STORAGE_ENGINE = semantic_config.get("storage_engine", "faiss")

# Base directories
BASE_DIR = Path(sys_path)
MEMORY_DIR = BASE_DIR / "data" / "memory"
MEMORY_DIR.mkdir(exist_ok=True, parents=True)

class MemoryItem:
    """Base class for memory items"""
    
    def __init__(self, content: str, source: str, timestamp: Optional[datetime] = None, metadata: Optional[Dict[str, Any]] = None):
        self.content = content
        self.source = source  # e.g., "conversation", "user_profile", "document"
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}
        self.importance = self.calculate_importance()
        self.last_accessed = self.timestamp
        self.access_count = 0
    
    def calculate_importance(self) -> float:
        """Calculate importance score for this memory item"""
        # Base importance is 0.5
        importance = 0.5
        
        # Adjust based on metadata if available
        if self.metadata:
            # Emotional content is more important
            if "emotion" in self.metadata:
                emotion_score = {
                    "joy": 0.6,
                    "sadness": 0.7,
                    "anger": 0.8,
                    "fear": 0.8,
                    "surprise": 0.7,
                    "disgust": 0.6,
                    "neutral": 0.5
                }.get(self.metadata["emotion"], 0.5)
                importance = max(importance, emotion_score)
            
            # User preferences are important
            if "user_preference" in self.metadata:
                importance += 0.2
            
            # Personal information is important
            if "personal_info" in self.metadata:
                importance += 0.3
            
            # Explicit importance flag
            if "importance" in self.metadata:
                importance = max(importance, float(self.metadata["importance"]))
        
        return min(importance, 1.0)  # Cap at 1.0
    
    def access(self) -> None:
        """Record an access to this memory item"""
        self.last_accessed = datetime.now()
        self.access_count += 1
        
        # Increase importance with access
        access_boost = min(0.1 * (self.access_count / 10), 0.3)  # Max boost of 0.3
        self.importance = min(self.importance + access_boost, 1.0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "content": self.content,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "importance": self.importance,
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryItem':
        """Create from dictionary"""
        item = cls(
            content=data["content"],
            source=data["source"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data["metadata"]
        )
        item.importance = data["importance"]
        item.last_accessed = datetime.fromisoformat(data["last_accessed"])
        item.access_count = data["access_count"]
        return item

class ShortTermMemory:
    """Short-term memory for recent conversations"""
    
    def __init__(self, capacity: int = 20):
        self.capacity = capacity
        self.items = []  # List of MemoryItem objects
    
    def add(self, item: MemoryItem) -> None:
        """Add an item to short-term memory"""
        self.items.append(item)
        
        # Keep only the most recent items within capacity
        if len(self.items) > self.capacity:
            self.items = self.items[-self.capacity:]
    
    def get_recent(self, count: int = 5) -> List[MemoryItem]:
        """Get the most recent items"""
        return self.items[-count:] if len(self.items) >= count else self.items
    
    def get_by_source(self, source: str) -> List[MemoryItem]:
        """Get items by source"""
        return [item for item in self.items if item.source == source]
    
    def clear(self) -> None:
        """Clear short-term memory"""
        self.items = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "capacity": self.capacity,
            "items": [item.to_dict() for item in self.items]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ShortTermMemory':
        """Create from dictionary"""
        memory = cls(capacity=data["capacity"])
        memory.items = [MemoryItem.from_dict(item) for item in data["items"]]
        return memory

class MediumTermMemory:
    """Medium-term memory for the current session"""
    
    def __init__(self, capacity: int = 100, session_id: Optional[str] = None):
        self.capacity = capacity
        self.session_id = session_id or datetime.now().strftime("%Y%m%d%H%M%S")
        self.items = []  # List of MemoryItem objects
        self.summary = ""
        self.start_time = datetime.now()
        self.last_updated = self.start_time
    
    def add(self, item: MemoryItem) -> None:
        """Add an item to medium-term memory"""
        self.items.append(item)
        self.last_updated = datetime.now()
        
        # Keep only the most important items within capacity
        if len(self.items) > self.capacity:
            # Sort by importance and recency
            self.items.sort(key=lambda x: (x.importance, x.timestamp), reverse=True)
            self.items = self.items[:self.capacity]
    
    def update_summary(self, summary: str) -> None:
        """Update the session summary"""
        self.summary = summary
        self.last_updated = datetime.now()
    
    def get_items_by_importance(self, threshold: float = 0.7) -> List[MemoryItem]:
        """Get items by importance threshold"""
        return [item for item in self.items if item.importance >= threshold]
    
    def get_items_by_timeframe(self, start_time: datetime, end_time: datetime) -> List[MemoryItem]:
        """Get items within a specific timeframe"""
        return [item for item in self.items if start_time <= item.timestamp <= end_time]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "capacity": self.capacity,
            "session_id": self.session_id,
            "items": [item.to_dict() for item in self.items],
            "summary": self.summary,
            "start_time": self.start_time.isoformat(),
            "last_updated": self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MediumTermMemory':
        """Create from dictionary"""
        memory = cls(
            capacity=data["capacity"],
            session_id=data["session_id"]
        )
        memory.items = [MemoryItem.from_dict(item) for item in data["items"]]
        memory.summary = data["summary"]
        memory.start_time = datetime.fromisoformat(data["start_time"])
        memory.last_updated = datetime.fromisoformat(data["last_updated"])
        return memory

class LongTermMemory:
    """Long-term memory for persistent user information"""
    
    def __init__(self, user_id: str, capacity: int = 1000):
        self.user_id = user_id
        self.capacity = capacity
        self.items = []  # List of MemoryItem objects
        self.categories = {}  # Map of category -> list of items
        self.last_consolidated = datetime.now()
    
    def add(self, item: MemoryItem, category: Optional[str] = None) -> None:
        """Add an item to long-term memory"""
        self.items.append(item)
        
        # Add to category if provided
        if category:
            if category not in self.categories:
                self.categories[category] = []
            self.categories[category].append(item)
        
        # Keep only the most important items within capacity
        if len(self.items) > self.capacity:
            self._consolidate_memory()
    
    def _consolidate_memory(self) -> None:
        """Consolidate memory by removing less important items"""
        # Sort by importance, access count, and recency
        self.items.sort(key=lambda x: (x.importance, x.access_count, x.last_accessed), reverse=True)
        
        # Keep only within capacity
        self.items = self.items[:self.capacity]
        
        # Update categories
        for category, items in self.categories.items():
            self.categories[category] = [item for item in items if item in self.items]
        
        self.last_consolidated = datetime.now()
    
    def get_by_category(self, category: str) -> List[MemoryItem]:
        """Get items by category"""
        return self.categories.get(category, [])
    
    def get_by_importance(self, threshold: float = 0.8) -> List[MemoryItem]:
        """Get items by importance threshold"""
        return [item for item in self.items if item.importance >= threshold]
    
    def get_by_recency(self, days: int = 7) -> List[MemoryItem]:
        """Get items by recency"""
        cutoff = datetime.now() - timedelta(days=days)
        return [item for item in self.items if item.timestamp >= cutoff]
    
    def search(self, query: str) -> List[MemoryItem]:
        """Simple keyword search in long-term memory"""
        query_lower = query.lower()
        results = []
        
        for item in self.items:
            if query_lower in item.content.lower():
                # Record access
                item.access()
                results.append(item)
        
        return results
    
    def save(self, directory: Optional[str] = None) -> str:
        """Save long-term memory to disk"""
        save_dir = Path(directory) if directory else MEMORY_DIR / self.user_id
        save_dir.mkdir(exist_ok=True, parents=True)
        
        file_path = save_dir / "long_term_memory.json"
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({
                "user_id": self.user_id,
                "capacity": self.capacity,
                "items": [item.to_dict() for item in self.items],
                "categories": {k: [item.to_dict() for item in v] for k, v in self.categories.items()},
                "last_consolidated": self.last_consolidated.isoformat()
            }, f, indent=2)
        
        return str(file_path)
    
    @classmethod
    def load(cls, user_id: str, directory: Optional[str] = None) -> 'LongTermMemory':
        """Load long-term memory from disk"""
        load_dir = Path(directory) if directory else MEMORY_DIR / user_id
        file_path = load_dir / "long_term_memory.json"
        
        if not file_path.exists():
            return cls(user_id=user_id)
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            memory = cls(user_id=data["user_id"], capacity=data["capacity"])
            memory.items = [MemoryItem.from_dict(item) for item in data["items"]]
            memory.categories = {k: [MemoryItem.from_dict(item) for item in v] for k, v in data["categories"].items()}
            memory.last_consolidated = datetime.fromisoformat(data["last_consolidated"])
            
            return memory
        except Exception as e:
            logger.error(f"Error loading long-term memory: {str(e)}")
            return cls(user_id=user_id)

class SemanticMemory:
    """Semantic memory using vector embeddings for similarity search"""
    
    def __init__(self, user_id: str, embedding_model: str = EMBEDDING_MODEL):
        self.user_id = user_id
        self.embedding_model_name = embedding_model
        self.embedding_model = None
        self.index = None
        self.items = []  # List of MemoryItem objects
        self.embeddings = []  # List of embedding vectors
        
        # Initialize embedding model
        self._initialize_embedding_model()
        
        # Initialize FAISS index
        self._initialize_index()
    
    def _initialize_embedding_model(self) -> None:
        """Initialize the embedding model"""
        try:
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            logger.info(f"Initialized embedding model: {self.embedding_model_name}")
        except Exception as e:
            logger.error(f"Error initializing embedding model: {str(e)}")
    
    def _initialize_index(self) -> None:
        """Initialize the FAISS index"""
        if self.embedding_model is None:
            return
        
        try:
            # Get embedding dimension
            dummy_embedding = self.embedding_model.encode(["test"])[0]
            dimension = len(dummy_embedding)
            
            # Create index
            self.index = faiss.IndexFlatL2(dimension)
            logger.info(f"Initialized FAISS index with dimension: {dimension}")
        except Exception as e:
            logger.error(f"Error initializing FAISS index: {str(e)}")
    
    def add(self, item: MemoryItem) -> None:
        """Add an item to semantic memory"""
        if self.embedding_model is None or self.index is None:
            logger.warning("Embedding model or index not initialized")
            return
        
        try:
            # Generate embedding
            embedding = self.embedding_model.encode([item.content])[0]
            
            # Add to index
            self.index.add(np.array([embedding], dtype=np.float32))
            
            # Store item and embedding
            self.items.append(item)
            self.embeddings.append(embedding)
            
            logger.debug(f"Added item to semantic memory: {item.content[:50]}...")
        except Exception as e:
            logger.error(f"Error adding item to semantic memory: {str(e)}")
    
    def search(self, query: str, k: int = 5) -> List[Tuple[MemoryItem, float]]:
        """Search for similar items"""
        if self.embedding_model is None or self.index is None or not self.items:
            logger.warning("Embedding model or index not initialized or no items")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])[0]
            
            # Search index
            distances, indices = self.index.search(np.array([query_embedding], dtype=np.float32), k=min(k, len(self.items)))
            
            # Get results
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.items):
                    item = self.items[idx]
                    distance = distances[0][i]
                    
                    # Convert distance to similarity score (1.0 is most similar)
                    similarity = 1.0 / (1.0 + distance)
                    
                    # Record access
                    item.access()
                    
                    results.append((item, similarity))
            
            return results
        except Exception as e:
            logger.error(f"Error searching semantic memory: {str(e)}")
            return []
    
    def save(self, directory: Optional[str] = None) -> str:
        """Save semantic memory to disk"""
        save_dir = Path(directory) if directory else MEMORY_DIR / self.user_id
        save_dir.mkdir(exist_ok=True, parents=True)
        
        # Save items
        items_path = save_dir / "semantic_memory_items.json"
        with open(items_path, "w", encoding="utf-8") as f:
            json.dump({
                "user_id": self.user_id,
                "embedding_model": self.embedding_model_name,
                "items": [item.to_dict() for item in self.items]
            }, f, indent=2)
        
        # Save index if available
        if self.index is not None:
            index_path = save_dir / "semantic_memory_index.faiss"
            try:
                faiss.write_index(self.index, str(index_path))
            except Exception as e:
                logger.error(f"Error saving FAISS index: {str(e)}")
        
        # Save embeddings
        embeddings_path = save_dir / "semantic_memory_embeddings.pkl"
        with open(embeddings_path, "wb") as f:
            pickle.dump(self.embeddings, f)
        
        return str(save_dir)
    
    @classmethod
    def load(cls, user_id: str, directory: Optional[str] = None) -> 'SemanticMemory':
        """Load semantic memory from disk"""
        load_dir = Path(directory) if directory else MEMORY_DIR / user_id
        items_path = load_dir / "semantic_memory_items.json"
        index_path = load_dir / "semantic_memory_index.faiss"
        embeddings_path = load_dir / "semantic_memory_embeddings.pkl"
        
        if not items_path.exists():
            return cls(user_id=user_id)
        
        try:
            # Load items
            with open(items_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            memory = cls(user_id=data["user_id"], embedding_model=data["embedding_model"])
            memory.items = [MemoryItem.from_dict(item) for item in data["items"]]
            
            # Load index if available
            if index_path.exists():
                memory.index = faiss.read_index(str(index_path))
            
            # Load embeddings
            if embeddings_path.exists():
                with open(embeddings_path, "rb") as f:
                    memory.embeddings = pickle.load(f)
            
            return memory
        except Exception as e:
            logger.error(f"Error loading semantic memory: {str(e)}")
            return cls(user_id=user_id)

class HierarchicalMemory:
    """Hierarchical memory system combining different memory types"""
    
    def __init__(self, user_id: str, session_id: Optional[str] = None):
        self.user_id = user_id
        self.session_id = session_id or datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Initialize different memory types
        self.short_term = ShortTermMemory()
        self.medium_term = MediumTermMemory(session_id=self.session_id)
        self.long_term = LongTermMemory.load(user_id)
        self.semantic = SemanticMemory(user_id)
        
        # Track memory statistics
        self.stats = {
            "items_added": 0,
            "items_retrieved": 0,
            "searches_performed": 0,
            "last_save": None
        }
    
    def add_memory(self, content: str, source: str, metadata: Optional[Dict[str, Any]] = None) -> MemoryItem:
        """
        Add a memory item to all memory levels
        
        Args:
            content: The content to remember
            source: The source of the memory (e.g., "conversation", "user_profile")
            metadata: Additional metadata for the memory
            
        Returns:
            The created memory item
        """
        # Create memory item
        item = MemoryItem(content=content, source=source, metadata=metadata)
        
        # Add to all memory levels
        self.short_term.add(item)
        self.medium_term.add(item)
        
        # Only add important items to long-term memory
        if item.importance >= 0.6:
            category = metadata.get("category") if metadata else None
            self.long_term.add(item, category=category)
        
        # Add to semantic memory
        self.semantic.add(item)
        
        # Update stats
        self.stats["items_added"] += 1
        
        return item
    
    def get_relevant_memories(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Get memories relevant to a query from all memory levels
        
        Args:
            query: The query to search for
            k: Number of results to return from each memory level
            
        Returns:
            List of relevant memories with their sources
        """
        results = []
        
        # Update stats
        self.stats["searches_performed"] += 1
        
        # First check short-term memory (most recent conversations)
        short_term_results = self.short_term.get_recent(k)
        for item in short_term_results:
            results.append({
                "content": item.content,
                "source": item.source,
                "timestamp": item.timestamp,
                "memory_type": "short_term",
                "importance": item.importance,
                "metadata": item.metadata
            })
        
        # Then check semantic memory (most relevant by meaning)
        semantic_results = self.semantic.search(query, k)
        for item, similarity in semantic_results:
            # Only include if similarity is high enough
            if similarity >= 0.7:
                results.append({
                    "content": item.content,
                    "source": item.source,
                    "timestamp": item.timestamp,
                    "memory_type": "semantic",
                    "importance": item.importance,
                    "similarity": similarity,
                    "metadata": item.metadata
                })
        
        # Then check long-term memory (important persistent information)
        long_term_results = self.long_term.search(query)[:k]
        for item in long_term_results:
            results.append({
                "content": item.content,
                "source": item.source,
                "timestamp": item.timestamp,
                "memory_type": "long_term",
                "importance": item.importance,
                "metadata": item.metadata
            })
        
        # Update stats
        self.stats["items_retrieved"] += len(results)
        
        # Sort by importance and recency
        results.sort(key=lambda x: (x.get("importance", 0), x.get("timestamp")), reverse=True)
        
        return results
    
    def get_memory_by_category(self, category: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get memories by category from long-term memory"""
        items = self.long_term.get_by_category(category)[:limit]
        
        results = []
        for item in items:
            results.append({
                "content": item.content,
                "source": item.source,
                "timestamp": item.timestamp,
                "memory_type": "long_term",
                "importance": item.importance,
                "metadata": item.metadata
            })
        
        # Update stats
        self.stats["items_retrieved"] += len(results)
        
        return results
    
    def get_recent_memories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent memories from short-term memory"""
        items = self.short_term.get_recent(limit)
        
        results = []
        for item in items:
            results.append({
                "content": item.content,
                "source": item.source,
                "timestamp": item.timestamp,
                "memory_type": "short_term",
                "importance": item.importance,
                "metadata": item.metadata
            })
        
        # Update stats
        self.stats["items_retrieved"] += len(results)
        
        return results
    
    def save(self) -> None:
        """Save all memory levels to disk"""
        # Save long-term memory
        self.long_term.save()
        
        # Save semantic memory
        self.semantic.save()
        
        # Save medium-term memory for the session
        session_dir = MEMORY_DIR / self.user_id / "sessions"
        session_dir.mkdir(exist_ok=True, parents=True)
        
        with open(session_dir / f"{self.session_id}.json", "w", encoding="utf-8") as f:
            json.dump(self.medium_term.to_dict(), f, indent=2)
        
        # Update stats
        self.stats["last_save"] = datetime.now().isoformat()
        
        # Save stats
        with open(MEMORY_DIR / self.user_id / "memory_stats.json", "w", encoding="utf-8") as f:
            json.dump(self.stats, f, indent=2)
    
    @classmethod
    def load(cls, user_id: str, session_id: Optional[str] = None) -> 'HierarchicalMemory':
        """Load hierarchical memory from disk"""
        memory = cls(user_id=user_id, session_id=session_id)
        
        # Long-term and semantic memories are already loaded in __init__
        
        # Load medium-term memory for the session if it exists
        if session_id:
            session_file = MEMORY_DIR / user_id / "sessions" / f"{session_id}.json"
            if session_file.exists():
                try:
                    with open(session_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    memory.medium_term = MediumTermMemory.from_dict(data)
                except Exception as e:
                    logger.error(f"Error loading medium-term memory: {str(e)}")
        
        # Load stats if they exist
        stats_file = MEMORY_DIR / user_id / "memory_stats.json"
        if stats_file.exists():
            try:
                with open(stats_file, "r", encoding="utf-8") as f:
                    memory.stats = json.load(f)
            except Exception as e:
                logger.error(f"Error loading memory stats: {str(e)}")
        
        return memory
