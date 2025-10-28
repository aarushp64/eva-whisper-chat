"""
Memory Manager

This module provides a central interface for managing different memory types:
1. Hierarchical memory (short-term, medium-term, long-term, semantic)
2. Knowledge bases
3. User profiles
4. Conversation context
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
from pathlib import Path
import uuid

# Import memory systems
from memory.hierarchical_memory import HierarchicalMemory, MemoryItem
from memory.conversation_memory import ConversationMemory, ThreadedMemory

# Import NLP and ML modules for analysis
from nlp.entity_recognition_advanced import extract_entities_with_context
from nlp.intent_recognition_advanced import recognize_intent_with_context
from ml.user_personalization import UserPersonalizationModel

# Import advanced features configuration
sys_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if sys_path not in os.sys.path:
    os.sys.path.append(sys_path)

from config.advanced_features import MEMORY_CONFIG, is_feature_enabled

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Base directories
BASE_DIR = Path(sys_path)
DATA_DIR = BASE_DIR / "data"
PROFILES_DIR = DATA_DIR / "profiles"
KNOWLEDGE_DIR = DATA_DIR / "knowledge_bases"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
PROFILES_DIR.mkdir(exist_ok=True)
KNOWLEDGE_DIR.mkdir(exist_ok=True)

class UserProfile:
    """User profile information"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.profile_data = {
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "preferences": {},
            "personal_info": {},
            "interaction_history": {
                "session_count": 0,
                "last_session": None,
                "total_messages": 0,
                "favorite_topics": []
            }
        }
        self.load()
    
    def update_preference(self, key: str, value: Any) -> None:
        """Update a user preference"""
        self.profile_data["preferences"][key] = value
        self.profile_data["last_updated"] = datetime.now().isoformat()
        self.save()
    
    def update_personal_info(self, key: str, value: Any) -> None:
        """Update personal information"""
        self.profile_data["personal_info"][key] = value
        self.profile_data["last_updated"] = datetime.now().isoformat()
        self.save()
    
    def record_session(self, session_id: str) -> None:
        """Record a new session"""
        self.profile_data["interaction_history"]["session_count"] += 1
        self.profile_data["interaction_history"]["last_session"] = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }
        self.profile_data["last_updated"] = datetime.now().isoformat()
        self.save()
    
    def record_message(self, topic: Optional[str] = None) -> None:
        """Record a message, optionally with a topic"""
        self.profile_data["interaction_history"]["total_messages"] += 1
        
        if topic:
            # Update favorite topics
            topics = self.profile_data["interaction_history"]["favorite_topics"]
            topic_found = False
            
            for t in topics:
                if t["topic"] == topic:
                    t["count"] += 1
                    topic_found = True
                    break
            
            if not topic_found:
                topics.append({"topic": topic, "count": 1})
            
            # Sort by count
            topics.sort(key=lambda x: x["count"], reverse=True)
            
            # Keep only top 10
            self.profile_data["interaction_history"]["favorite_topics"] = topics[:10]
        
        self.profile_data["last_updated"] = datetime.now().isoformat()
        self.save()
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference"""
        return self.profile_data["preferences"].get(key, default)
    
    def get_personal_info(self, key: str, default: Any = None) -> Any:
        """Get personal information"""
        return self.profile_data["personal_info"].get(key, default)
    
    def get_favorite_topics(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get favorite topics"""
        return self.profile_data["interaction_history"]["favorite_topics"][:limit]
    
    def save(self) -> None:
        """Save profile to disk"""
        profile_path = PROFILES_DIR / f"{self.user_id}.json"
        
        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(self.profile_data, f, indent=2)
    
    def load(self) -> None:
        """Load profile from disk"""
        profile_path = PROFILES_DIR / f"{self.user_id}.json"
        
        if profile_path.exists():
            try:
                with open(profile_path, "r", encoding="utf-8") as f:
                    self.profile_data = json.load(f)
            except Exception as e:
                logger.error(f"Error loading user profile: {str(e)}")

class KnowledgeBase:
    """Knowledge base for storing domain-specific information"""
    
    def __init__(self, name: str):
        self.name = name
        self.kb_data = {
            "name": name,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "description": "",
            "entities": [],
            "relationships": [],
            "metadata": {}
        }
        self.load()
    
    def add_entity(self, entity: Dict[str, Any]) -> str:
        """
        Add an entity to the knowledge base
        
        Args:
            entity: Entity data with at least 'name' and 'type'
            
        Returns:
            Entity ID
        """
        # Generate ID if not provided
        if "id" not in entity:
            entity["id"] = str(uuid.uuid4())
        
        # Add created timestamp
        if "created_at" not in entity:
            entity["created_at"] = datetime.now().isoformat()
        
        # Add or update last_updated
        entity["last_updated"] = datetime.now().isoformat()
        
        # Check if entity already exists
        for i, existing in enumerate(self.kb_data["entities"]):
            if existing["id"] == entity["id"]:
                # Update existing entity
                self.kb_data["entities"][i] = entity
                self.kb_data["last_updated"] = datetime.now().isoformat()
                self.save()
                return entity["id"]
        
        # Add new entity
        self.kb_data["entities"].append(entity)
        self.kb_data["last_updated"] = datetime.now().isoformat()
        self.save()
        
        return entity["id"]
    
    def add_relationship(self, relationship: Dict[str, Any]) -> str:
        """
        Add a relationship between entities
        
        Args:
            relationship: Relationship data with 'source_id', 'target_id', and 'type'
            
        Returns:
            Relationship ID
        """
        # Generate ID if not provided
        if "id" not in relationship:
            relationship["id"] = str(uuid.uuid4())
        
        # Add created timestamp
        if "created_at" not in relationship:
            relationship["created_at"] = datetime.now().isoformat()
        
        # Add or update last_updated
        relationship["last_updated"] = datetime.now().isoformat()
        
        # Check if relationship already exists
        for i, existing in enumerate(self.kb_data["relationships"]):
            if existing["id"] == relationship["id"]:
                # Update existing relationship
                self.kb_data["relationships"][i] = relationship
                self.kb_data["last_updated"] = datetime.now().isoformat()
                self.save()
                return relationship["id"]
        
        # Add new relationship
        self.kb_data["relationships"].append(relationship)
        self.kb_data["last_updated"] = datetime.now().isoformat()
        self.save()
        
        return relationship["id"]
    
    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get an entity by ID"""
        for entity in self.kb_data["entities"]:
            if entity["id"] == entity_id:
                return entity
        return None
    
    def get_entities_by_type(self, entity_type: str) -> List[Dict[str, Any]]:
        """Get entities by type"""
        return [e for e in self.kb_data["entities"] if e["type"] == entity_type]
    
    def search_entities(self, query: str) -> List[Dict[str, Any]]:
        """Search entities by name or attributes"""
        query_lower = query.lower()
        results = []
        
        for entity in self.kb_data["entities"]:
            # Check name
            if "name" in entity and query_lower in entity["name"].lower():
                results.append(entity)
                continue
            
            # Check attributes
            if "attributes" in entity:
                for key, value in entity["attributes"].items():
                    if isinstance(value, str) and query_lower in value.lower():
                        results.append(entity)
                        break
        
        return results
    
    def get_related_entities(self, entity_id: str) -> List[Dict[str, Any]]:
        """Get entities related to a specific entity"""
        related = []
        
        # Find relationships involving this entity
        for rel in self.kb_data["relationships"]:
            if rel["source_id"] == entity_id:
                # Get target entity
                target = self.get_entity(rel["target_id"])
                if target:
                    related.append({
                        "entity": target,
                        "relationship": rel["type"],
                        "direction": "outgoing"
                    })
            
            elif rel["target_id"] == entity_id:
                # Get source entity
                source = self.get_entity(rel["source_id"])
                if source:
                    related.append({
                        "entity": source,
                        "relationship": rel["type"],
                        "direction": "incoming"
                    })
        
        return related
    
    def save(self) -> None:
        """Save knowledge base to disk"""
        kb_path = KNOWLEDGE_DIR / f"{self.name}.json"
        
        with open(kb_path, "w", encoding="utf-8") as f:
            json.dump(self.kb_data, f, indent=2)
    
    def load(self) -> None:
        """Load knowledge base from disk"""
        kb_path = KNOWLEDGE_DIR / f"{self.name}.json"
        
        if kb_path.exists():
            try:
                with open(kb_path, "r", encoding="utf-8") as f:
                    self.kb_data = json.load(f)
            except Exception as e:
                logger.error(f"Error loading knowledge base: {str(e)}")

class MemoryManager:
    """Central manager for all memory systems"""
    
    def __init__(self):
        self.hierarchical_memories = {}  # user_id -> HierarchicalMemory
        self.conversation_memories = {}  # user_id -> ConversationMemory
        self.threaded_memories = {}  # user_id -> ThreadedMemory
        self.user_profiles = {}  # user_id -> UserProfile
        self.knowledge_bases = {}  # name -> KnowledgeBase
        
        # Load available knowledge bases
        self._load_knowledge_bases()
    
    def _load_knowledge_bases(self) -> None:
        """Load all available knowledge bases"""
        for kb_file in KNOWLEDGE_DIR.glob("*.json"):
            kb_name = kb_file.stem
            self.knowledge_bases[kb_name] = KnowledgeBase(kb_name)
    
    def get_hierarchical_memory(self, user_id: str, session_id: Optional[str] = None) -> HierarchicalMemory:
        """Get or create hierarchical memory for a user"""
        key = f"{user_id}:{session_id}" if session_id else user_id
        
        if key not in self.hierarchical_memories:
            self.hierarchical_memories[key] = HierarchicalMemory.load(user_id, session_id)
        
        return self.hierarchical_memories[key]
    
    def get_conversation_memory(self, user_id: str, chat_id: Optional[str] = None) -> ConversationMemory:
        """Get or create conversation memory for a user"""
        key = f"{user_id}:{chat_id}" if chat_id else user_id
        
        if key not in self.conversation_memories:
            self.conversation_memories[key] = ConversationMemory(user_id, chat_id)
        
        return self.conversation_memories[key]
    
    def get_threaded_memory(self, user_id: str) -> ThreadedMemory:
        """Get or create threaded memory for a user"""
        if user_id not in self.threaded_memories:
            self.threaded_memories[user_id] = ThreadedMemory(user_id)
        
        return self.threaded_memories[user_id]
    
    def get_user_profile(self, user_id: str) -> UserProfile:
        """Get or create user profile"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserProfile(user_id)
        
        return self.user_profiles[user_id]
    
    def get_knowledge_base(self, name: str) -> KnowledgeBase:
        """Get or create knowledge base"""
        if name not in self.knowledge_bases:
            self.knowledge_bases[name] = KnowledgeBase(name)
        
        return self.knowledge_bases[name]
    
    def add_memory(self, user_id: str, content: str, source: str, metadata: Optional[Dict[str, Any]] = None, session_id: Optional[str] = None) -> None:
        """
        Add a memory item to hierarchical memory
        
        Args:
            user_id: User ID
            content: Memory content
            source: Memory source
            metadata: Additional metadata
            session_id: Optional session ID
        """
        # Get hierarchical memory
        memory = self.get_hierarchical_memory(user_id, session_id)
        
        # Add memory
        memory.add_memory(content, source, metadata)
        
        # Save periodically (every 10 items)
        if memory.stats["items_added"] % 10 == 0:
            memory.save()
    
    def consolidate_memory(self, user_id: str, chat_id: Optional[str] = None) -> None:
        """
        Consolidate memory by moving important information from short-term to long-term memory
        """
        conversation_memory = self.get_conversation_memory(user_id, chat_id)
        hierarchical_memory = self.get_hierarchical_memory(user_id, chat_id)
        user_profile = self.get_user_profile(user_id)
        personalization_model = UserPersonalizationModel.load(user_id)

        # Analyze conversation history to identify key information
        for message in conversation_memory.get_full_history():
            message_content = message["content"]
            
            # Extract entities
            entities = extract_entities_with_context(message_content, context={"user_profile": user_profile.profile_data})
            for entity in entities:
                hierarchical_memory.add_memory(
                    content=entity["text"],
                    source=f"entity:{entity['label']}",
                    metadata=entity,
                    session_id=chat_id
                )
            
            # Recognize intent
            intent_result = recognize_intent_with_context(message_content, method="ensemble", context={"user_profile": user_profile.profile_data})
            if intent_result and intent_result.get("intent"):
                hierarchical_memory.add_memory(
                    content=intent_result["intent"],
                    source="intent",
                    metadata=intent_result,
                    session_id=chat_id
                )
            
            # Update user personalization model
            personalization_model.add_message(message)
        
        # Cluster topics and update user profile with interests
        if len(personalization_model.message_history) > 10: # Only cluster if enough messages
            topic_clusters = personalization_model.cluster_topics()
            if topic_clusters:
                user_profile.update_preference("favorite_topics", topic_clusters.get("cluster_summaries"))
                
            # Predict user interests and response style
            user_interests = personalization_model.predict_user_interests()
            if user_interests:
                user_profile.update_preference("predicted_interests", user_interests)
            
            response_style = personalization_model.predict_response_style()
            if response_style:
                user_profile.update_preference("predicted_response_style", response_style)
        
        # Save personalization model and user profile
        personalization_model.save()
        user_profile.save()
        
        logger.info(f"Consolidated memory for user {user_id} and chat {chat_id}")

    def get_contextual_memories(self, user_id: str, query: str, chat_id: Optional[str] = None, k: int = 5) -> Dict[str, Any]:
        """
        Get relevant contextual memories for a given query, including:
        - Relevant hierarchical memories (long-term, semantic)
        - User profile information
        - Relevant knowledge base entries
        - Recent conversation history
        
        Args:
            user_id: User ID
            query: The current user query/message
            chat_id: Optional chat ID for conversation memory
            k: Number of relevant items to retrieve from each source
            
        Returns:
            A dictionary containing various types of contextual information.
        """
        context = {}
        
        # 1. Get relevant hierarchical memories (long-term and semantic)
        hierarchical_memory = self.get_hierarchical_memory(user_id, chat_id)
        relevant_h_memories = hierarchical_memory.get_relevant_memories(query, k=k)
        context["hierarchical_memories"] = relevant_h_memories
        
        # 2. Get user profile information
        user_profile = self.get_user_profile(user_id)
        context["user_profile"] = user_profile.profile_data
        
        # 3. Search knowledge bases for relevant information
        # This can be expanded to search specific KBs based on query/context
        relevant_kb_entities = self.search_knowledge_base(query)
        context["knowledge_base_entities"] = relevant_kb_entities
        
        # 4. Get recent conversation history (short-term memory)
        conversation_memory = self.get_conversation_memory(user_id, chat_id)
        recent_conversation = conversation_memory.get_recent_messages(n=k)
        context["recent_conversation"] = recent_conversation
        
        # 5. Get user's predicted interests and response style
        personalization_model = UserPersonalizationModel.load(user_id)
        context["predicted_interests"] = user_profile.get_preference("predicted_interests", {})
        context["predicted_response_style"] = user_profile.get_preference("predicted_response_style", "empathetic")
        
        return context

    def add_conversation_message(self, user_id: str, message: Dict[str, Any], chat_id: Optional[str] = None) -> None:
        """
        Add a message to conversation memory
        
        Args:
            user_id: User ID
            message: Message object with sender, content, and timestamp
            chat_id: Optional chat ID
        """
        # Get conversation memory
        memory = self.get_conversation_memory(user_id, chat_id)
        
        # Add message
        memory.add_message(message)
        
        # Also add to hierarchical memory
        metadata = {
            "message_id": message.get("id", str(uuid.uuid4())),
            "chat_id": chat_id,
            "category": "conversation"
        }
        
        self.add_memory(
            user_id=user_id,
            content=message["content"],
            source=f"conversation:{message['sender']}",
            metadata=metadata,
            session_id=chat_id
        )
        
        # Update user profile
        profile = self.get_user_profile(user_id)
        profile.record_message(topic=message.get("topic"))
    
    def get_relevant_context(self, user_id: str, query: str, k: int = 5, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get relevant context for a query
        
        Args:
            user_id: User ID
            query: Query text
            k: Number of results to return
            session_id: Optional session ID
            
        Returns:
            Dictionary with relevant context from different memory systems
        """
        # Get hierarchical memory
        h_memory = self.get_hierarchical_memory(user_id, session_id)
        
        # Get relevant memories
        memories = h_memory.get_relevant_memories(query, k)
        
        # Get user profile
        profile = self.get_user_profile(user_id)
        
        # Compile context
        context = {
            "memories": memories,
            "user_profile": {
                "preferences": profile.profile_data["preferences"],
                "personal_info": profile.profile_data["personal_info"],
                "favorite_topics": profile.get_favorite_topics()
            },
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        return context

    def add_conversation_message(self, user_id: str, message: Dict[str, Any], chat_id: Optional[str] = None) -> None:
        """
        Add a message to conversation memory
        
        Args:
            user_id: User ID
            message: Message object with sender, content, and timestamp
            chat_id: Optional chat ID
        """
        # Get conversation memory
        memory = self.get_conversation_memory(user_id, chat_id)
        
        # Add message
        memory.add_message(message)
        
        # Also add to hierarchical memory
        metadata = {
            "message_id": message.get("id", str(uuid.uuid4())),
            "chat_id": chat_id,
            "category": "conversation"
        }
        
        self.add_memory(
            user_id=user_id,
            content=message["content"],
            source=f"conversation:{message['sender']}",
            metadata=metadata,
            session_id=chat_id
        )
        
        # Update user profile
        profile = self.get_user_profile(user_id)
        profile.record_message(topic=message.get("topic"))
    
    def get_relevant_context(self, user_id: str, query: str, k: int = 5, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get relevant context for a query
        
        Args:
            user_id: User ID
            query: Query text
            k: Number of results to return
            session_id: Optional session ID
            
        Returns:
            Dictionary with relevant context from different memory systems
        """
        # Get hierarchical memory
        h_memory = self.get_hierarchical_memory(user_id, session_id)
        
        # Get relevant memories
        memories = h_memory.get_relevant_memories(query, k)
        
        # Get user profile
        profile = self.get_user_profile(user_id)
        
        # Compile context
        context = {
            "memories": memories,
            "user_profile": {
                "preferences": profile.profile_data["preferences"],
                "personal_info": profile.profile_data["personal_info"],
                "favorite_topics": profile.get_favorite_topics()
            },
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        return context
    
    def search_knowledge_base(self, query: str, kb_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search knowledge bases for relevant information
        
        Args:
            query: Search query
            kb_name: Optional knowledge base name (if None, searches all)
            
        Returns:
            List of relevant entities
        """
        results = []
        
        if kb_name:
            # Search specific knowledge base
            if kb_name in self.knowledge_bases:
                kb = self.knowledge_bases[kb_name]
                entities = kb.search_entities(query)
                for entity in entities:
                    results.append({
                        "entity": entity,
                        "knowledge_base": kb_name
                    })
        else:
            # Search all knowledge bases
            for name, kb in self.knowledge_bases.items():
                entities = kb.search_entities(query)
                for entity in entities:
                    results.append({
                        "entity": entity,
                        "knowledge_base": name
                    })
        
        return results
    
    def save_all(self) -> None:
        """Save all memory systems to disk"""
        # Save hierarchical memories
        for memory in self.hierarchical_memories.values():
            memory.save()
        
        # Save user profiles
        for profile in self.user_profiles.values():
            profile.save()
        
        # Save knowledge bases
        for kb in self.knowledge_bases.values():
            kb.save()
        
        logger.info("Saved all memory systems to disk")

# Global memory manager instance
memory_manager = MemoryManager()

def get_memory_manager() -> MemoryManager:
    """Get the global memory manager instance"""
    return memory_manager
