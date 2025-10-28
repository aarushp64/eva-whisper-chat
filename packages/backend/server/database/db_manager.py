"""
Database Manager

This module provides a unified interface for database operations:
1. SQL databases (SQLite, PostgreSQL, MySQL)
2. Vector databases (FAISS, ChromaDB, Pinecone)
3. Document databases (MongoDB)
4. Key-value stores (Redis)
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path
import sys
import sqlite3
import uuid
from datetime import datetime

# Add server directory to path to allow imports from other modules
server_dir = Path(__file__).resolve().parent.parent
if str(server_dir) not in sys.path:
    sys.path.append(str(server_dir))

# Import configuration
from config.advanced_features import DATABASE_CONFIG, is_feature_enabled

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Base directories
BASE_DIR = server_dir
DATA_DIR = BASE_DIR / "data"
DB_DIR = DATA_DIR / "db"
DB_DIR.mkdir(exist_ok=True, parents=True)

class DatabaseManager:
    """Class for managing database connections and operations"""
    
    def __init__(self):
        # Load configuration
        self.config = DATABASE_CONFIG
        self.default_db_type = self.config.get("default_type", "sqlite")
        
        # Initialize connections
        self.connections = {}
        self.vector_stores = {}
        
        # Initialize default database
        self._initialize_default_db()
    
    def _initialize_default_db(self) -> None:
        """Initialize the default database"""
        try:
            if self.default_db_type == "sqlite":
                db_path = DB_DIR / "eva.db"
                conn = sqlite3.connect(str(db_path))
                self.connections["default"] = conn
                
                # Create tables if they don't exist
                self._create_default_tables(conn)
                
                logger.info(f"Initialized default SQLite database at {db_path}")
            
            elif self.default_db_type == "postgres":
                # PostgreSQL connection would be initialized here
                # using psycopg2 or SQLAlchemy
                if is_feature_enabled("database.postgres"):
                    try:
                        import psycopg2
                        # Connection parameters would come from config
                        # conn = psycopg2.connect(...)
                        logger.info("PostgreSQL support is enabled but not configured")
                    except ImportError:
                        logger.warning("PostgreSQL support is enabled but psycopg2 is not installed")
            
            elif self.default_db_type == "mysql":
                # MySQL connection would be initialized here
                if is_feature_enabled("database.mysql"):
                    try:
                        import mysql.connector
                        # Connection parameters would come from config
                        # conn = mysql.connector.connect(...)
                        logger.info("MySQL support is enabled but not configured")
                    except ImportError:
                        logger.warning("MySQL support is enabled but mysql-connector is not installed")
            
            # Initialize vector database if enabled
            if is_feature_enabled("database.vector_db"):
                self._initialize_vector_db()
            
            # Initialize document database if enabled
            if is_feature_enabled("database.document_db"):
                self._initialize_document_db()
            
            # Initialize key-value store if enabled
            if is_feature_enabled("database.key_value_store"):
                self._initialize_key_value_store()
                
        except Exception as e:
            logger.error(f"Error initializing default database: {str(e)}")
    
    def _create_default_tables(self, conn) -> None:
        """Create default tables in the database"""
        try:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT,
                email TEXT,
                created_at TEXT,
                last_login TEXT,
                preferences TEXT
            )
            ''')
            
            # Conversations table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                title TEXT,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            ''')
            
            # Messages table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT,
                sender TEXT,
                content TEXT,
                timestamp TEXT,
                metadata TEXT,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id)
            )
            ''')
            
            # Entities table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS entities (
                id TEXT PRIMARY KEY,
                name TEXT,
                entity_type TEXT,
                source TEXT,
                metadata TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            ''')
            
            # Entity relationships table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS entity_relationships (
                id TEXT PRIMARY KEY,
                source_entity_id TEXT,
                target_entity_id TEXT,
                relationship_type TEXT,
                metadata TEXT,
                created_at TEXT,
                FOREIGN KEY (source_entity_id) REFERENCES entities (id),
                FOREIGN KEY (target_entity_id) REFERENCES entities (id)
            )
            ''')
            
            # Analytics table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                event_type TEXT,
                event_data TEXT,
                timestamp TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            ''')
            
            conn.commit()
            logger.info("Created default tables in database")
            
        except Exception as e:
            logger.error(f"Error creating default tables: {str(e)}")
    
    def _initialize_vector_db(self) -> None:
        """Initialize vector database"""
        vector_db_type = self.config.get("vector_db", {}).get("type", "faiss")
        
        try:
            if vector_db_type == "faiss":
                try:
                    import faiss
                    logger.info("FAISS vector database initialized")
                except ImportError:
                    logger.warning("FAISS is enabled but not installed")
            
            elif vector_db_type == "chroma":
                try:
                    import chromadb
                    logger.info("ChromaDB vector database initialized")
                except ImportError:
                    logger.warning("ChromaDB is enabled but not installed")
            
            elif vector_db_type == "pinecone":
                try:
                    import pinecone
                    logger.info("Pinecone vector database initialized")
                except ImportError:
                    logger.warning("Pinecone is enabled but not installed")
                    
        except Exception as e:
            logger.error(f"Error initializing vector database: {str(e)}")
    
    def _initialize_document_db(self) -> None:
        """Initialize document database"""
        doc_db_type = self.config.get("document_db", {}).get("type", "mongodb")
        
        try:
            if doc_db_type == "mongodb":
                try:
                    import pymongo
                    logger.info("MongoDB document database initialized")
                except ImportError:
                    logger.warning("MongoDB is enabled but pymongo is not installed")
                    
        except Exception as e:
            logger.error(f"Error initializing document database: {str(e)}")
    
    def _initialize_key_value_store(self) -> None:
        """Initialize key-value store"""
        kv_store_type = self.config.get("key_value_store", {}).get("type", "redis")
        
        try:
            if kv_store_type == "redis":
                try:
                    import redis
                    logger.info("Redis key-value store initialized")
                except ImportError:
                    logger.warning("Redis is enabled but redis-py is not installed")
                    
        except Exception as e:
            logger.error(f"Error initializing key-value store: {str(e)}")
    
    def get_connection(self, connection_name: str = "default"):
        """Get a database connection by name"""
        return self.connections.get(connection_name)
    
    def create_user(self, username: str, email: Optional[str] = None) -> str:
        """
        Create a new user
        
        Args:
            username: Username
            email: Email address (optional)
            
        Returns:
            User ID
        """
        try:
            conn = self.get_connection()
            if not conn:
                return ""
            
            cursor = conn.cursor()
            
            # Generate user ID
            user_id = str(uuid.uuid4())
            
            # Current timestamp
            timestamp = datetime.now().isoformat()
            
            # Default preferences
            preferences = json.dumps({
                "communication_style": "balanced",
                "response_length": "medium",
                "formality": "casual"
            })
            
            # Insert user
            cursor.execute(
                "INSERT INTO users (id, username, email, created_at, last_login, preferences) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, username, email, timestamp, timestamp, preferences)
            )
            
            conn.commit()
            logger.info(f"Created user: {username} ({user_id})")
            
            return user_id
            
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return ""
    
    def get_user(self, user_id: str) -> Dict[str, Any]:
        """
        Get user by ID
        
        Args:
            user_id: User ID
            
        Returns:
            User data as dictionary
        """
        try:
            conn = self.get_connection()
            if not conn:
                return {}
            
            cursor = conn.cursor()
            
            # Query user
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            
            if not user:
                return {}
            
            # Convert to dictionary
            columns = [column[0] for column in cursor.description]
            user_dict = {columns[i]: user[i] for i in range(len(columns))}
            
            # Parse preferences
            if "preferences" in user_dict:
                try:
                    user_dict["preferences"] = json.loads(user_dict["preferences"])
                except:
                    user_dict["preferences"] = {}
            
            return user_dict
            
        except Exception as e:
            logger.error(f"Error getting user: {str(e)}")
            return {}
    
    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """
        Update user preferences
        
        Args:
            user_id: User ID
            preferences: User preferences
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            # Get current preferences
            cursor.execute("SELECT preferences FROM users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            
            if not result:
                return False
            
            # Parse current preferences
            try:
                current_prefs = json.loads(result[0])
            except:
                current_prefs = {}
            
            # Update preferences
            current_prefs.update(preferences)
            
            # Save updated preferences
            cursor.execute(
                "UPDATE users SET preferences = ? WHERE id = ?",
                (json.dumps(current_prefs), user_id)
            )
            
            conn.commit()
            logger.info(f"Updated preferences for user: {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating user preferences: {str(e)}")
            return False
    
    def create_conversation(self, user_id: str, title: Optional[str] = None) -> str:
        """
        Create a new conversation
        
        Args:
            user_id: User ID
            title: Conversation title (optional)
            
        Returns:
            Conversation ID
        """
        try:
            conn = self.get_connection()
            if not conn:
                return ""
            
            cursor = conn.cursor()
            
            # Generate conversation ID
            conversation_id = str(uuid.uuid4())
            
            # Current timestamp
            timestamp = datetime.now().isoformat()
            
            # Default title if not provided
            if not title:
                title = f"Conversation {timestamp}"
            
            # Insert conversation
            cursor.execute(
                "INSERT INTO conversations (id, user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (conversation_id, user_id, title, timestamp, timestamp)
            )
            
            conn.commit()
            logger.info(f"Created conversation: {title} ({conversation_id})")
            
            return conversation_id
            
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            return ""
    
    def get_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get conversation by ID
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Conversation data as dictionary
        """
        try:
            conn = self.get_connection()
            if not conn:
                return {}
            
            cursor = conn.cursor()
            
            # Query conversation
            cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
            conversation = cursor.fetchone()
            
            if not conversation:
                return {}
            
            # Convert to dictionary
            columns = [column[0] for column in cursor.description]
            conversation_dict = {columns[i]: conversation[i] for i in range(len(columns))}
            
            return conversation_dict
            
        except Exception as e:
            logger.error(f"Error getting conversation: {str(e)}")
            return {}
    
    def get_user_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all conversations for a user
        
        Args:
            user_id: User ID
            
        Returns:
            List of conversation dictionaries
        """
        try:
            conn = self.get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            
            # Query conversations
            cursor.execute("SELECT * FROM conversations WHERE user_id = ? ORDER BY updated_at DESC", (user_id,))
            conversations = cursor.fetchall()
            
            if not conversations:
                return []
            
            # Convert to dictionaries
            columns = [column[0] for column in cursor.description]
            conversation_dicts = []
            
            for conversation in conversations:
                conversation_dict = {columns[i]: conversation[i] for i in range(len(columns))}
                conversation_dicts.append(conversation_dict)
            
            return conversation_dicts
            
        except Exception as e:
            logger.error(f"Error getting user conversations: {str(e)}")
            return []
    
    def add_message(self, conversation_id: str, sender: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Add a message to a conversation
        
        Args:
            conversation_id: Conversation ID
            sender: Message sender (user or assistant)
            content: Message content
            metadata: Additional metadata
            
        Returns:
            Message ID
        """
        try:
            conn = self.get_connection()
            if not conn:
                return ""
            
            cursor = conn.cursor()
            
            # Generate message ID
            message_id = str(uuid.uuid4())
            
            # Current timestamp
            timestamp = datetime.now().isoformat()
            
            # Convert metadata to JSON string
            metadata_str = json.dumps(metadata) if metadata else "{}"
            
            # Insert message
            cursor.execute(
                "INSERT INTO messages (id, conversation_id, sender, content, timestamp, metadata) VALUES (?, ?, ?, ?, ?, ?)",
                (message_id, conversation_id, sender, content, timestamp, metadata_str)
            )
            
            # Update conversation updated_at
            cursor.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (timestamp, conversation_id)
            )
            
            conn.commit()
            logger.debug(f"Added message to conversation: {conversation_id}")
            
            return message_id
            
        except Exception as e:
            logger.error(f"Error adding message: {str(e)}")
            return ""
    
    def get_conversation_messages(self, conversation_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get messages for a conversation
        
        Args:
            conversation_id: Conversation ID
            limit: Maximum number of messages to return
            
        Returns:
            List of message dictionaries
        """
        try:
            conn = self.get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            
            # Query messages
            cursor.execute(
                "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC LIMIT ?",
                (conversation_id, limit)
            )
            messages = cursor.fetchall()
            
            if not messages:
                return []
            
            # Convert to dictionaries
            columns = [column[0] for column in cursor.description]
            message_dicts = []
            
            for message in messages:
                message_dict = {columns[i]: message[i] for i in range(len(columns))}
                
                # Parse metadata
                if "metadata" in message_dict:
                    try:
                        message_dict["metadata"] = json.loads(message_dict["metadata"])
                    except:
                        message_dict["metadata"] = {}
                
                message_dicts.append(message_dict)
            
            return message_dicts
            
        except Exception as e:
            logger.error(f"Error getting conversation messages: {str(e)}")
            return []
    
    def add_entity(self, name: str, entity_type: str, source: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Add an entity to the database
        
        Args:
            name: Entity name
            entity_type: Entity type
            source: Source of the entity
            metadata: Additional metadata
            
        Returns:
            Entity ID
        """
        try:
            conn = self.get_connection()
            if not conn:
                return ""
            
            cursor = conn.cursor()
            
            # Generate entity ID
            entity_id = str(uuid.uuid4())
            
            # Current timestamp
            timestamp = datetime.now().isoformat()
            
            # Convert metadata to JSON string
            metadata_str = json.dumps(metadata) if metadata else "{}"
            
            # Insert entity
            cursor.execute(
                "INSERT INTO entities (id, name, entity_type, source, metadata, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (entity_id, name, entity_type, source, metadata_str, timestamp, timestamp)
            )
            
            conn.commit()
            logger.info(f"Added entity: {name} ({entity_type})")
            
            return entity_id
            
        except Exception as e:
            logger.error(f"Error adding entity: {str(e)}")
            return ""
    
    def add_entity_relationship(self, source_entity_id: str, target_entity_id: str, relationship_type: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Add a relationship between entities
        
        Args:
            source_entity_id: Source entity ID
            target_entity_id: Target entity ID
            relationship_type: Type of relationship
            metadata: Additional metadata
            
        Returns:
            Relationship ID
        """
        try:
            conn = self.get_connection()
            if not conn:
                return ""
            
            cursor = conn.cursor()
            
            # Generate relationship ID
            relationship_id = str(uuid.uuid4())
            
            # Current timestamp
            timestamp = datetime.now().isoformat()
            
            # Convert metadata to JSON string
            metadata_str = json.dumps(metadata) if metadata else "{}"
            
            # Insert relationship
            cursor.execute(
                "INSERT INTO entity_relationships (id, source_entity_id, target_entity_id, relationship_type, metadata, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (relationship_id, source_entity_id, target_entity_id, relationship_type, metadata_str, timestamp)
            )
            
            conn.commit()
            logger.info(f"Added entity relationship: {source_entity_id} -> {relationship_type} -> {target_entity_id}")
            
            return relationship_id
            
        except Exception as e:
            logger.error(f"Error adding entity relationship: {str(e)}")
            return ""
    
    def search_entities(self, query: str, entity_type: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for entities
        
        Args:
            query: Search query
            entity_type: Filter by entity type (optional)
            limit: Maximum number of results
            
        Returns:
            List of entity dictionaries
        """
        try:
            conn = self.get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            
            # Build query
            sql = "SELECT * FROM entities WHERE name LIKE ?"
            params = [f"%{query}%"]
            
            if entity_type:
                sql += " AND entity_type = ?"
                params.append(entity_type)
            
            sql += " LIMIT ?"
            params.append(limit)
            
            # Execute query
            cursor.execute(sql, tuple(params))
            entities = cursor.fetchall()
            
            if not entities:
                return []
            
            # Convert to dictionaries
            columns = [column[0] for column in cursor.description]
            entity_dicts = []
            
            for entity in entities:
                entity_dict = {columns[i]: entity[i] for i in range(len(columns))}
                
                # Parse metadata
                if "metadata" in entity_dict:
                    try:
                        entity_dict["metadata"] = json.loads(entity_dict["metadata"])
                    except:
                        entity_dict["metadata"] = {}
                
                entity_dicts.append(entity_dict)
            
            return entity_dicts
            
        except Exception as e:
            logger.error(f"Error searching entities: {str(e)}")
            return []
    
    def get_entity_relationships(self, entity_id: str) -> List[Dict[str, Any]]:
        """
        Get relationships for an entity
        
        Args:
            entity_id: Entity ID
            
        Returns:
            List of relationship dictionaries
        """
        try:
            conn = self.get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            
            # Query relationships where entity is source or target
            cursor.execute(
                """
                SELECT r.*, 
                       s.name as source_name, s.entity_type as source_type,
                       t.name as target_name, t.entity_type as target_type
                FROM entity_relationships r
                JOIN entities s ON r.source_entity_id = s.id
                JOIN entities t ON r.target_entity_id = t.id
                WHERE r.source_entity_id = ? OR r.target_entity_id = ?
                """,
                (entity_id, entity_id)
            )
            relationships = cursor.fetchall()
            
            if not relationships:
                return []
            
            # Convert to dictionaries
            columns = [column[0] for column in cursor.description]
            relationship_dicts = []
            
            for relationship in relationships:
                relationship_dict = {columns[i]: relationship[i] for i in range(len(columns))}
                
                # Parse metadata
                if "metadata" in relationship_dict:
                    try:
                        relationship_dict["metadata"] = json.loads(relationship_dict["metadata"])
                    except:
                        relationship_dict["metadata"] = {}
                
                # Add direction
                relationship_dict["direction"] = "outgoing" if relationship_dict["source_entity_id"] == entity_id else "incoming"
                
                relationship_dicts.append(relationship_dict)
            
            return relationship_dicts
            
        except Exception as e:
            logger.error(f"Error getting entity relationships: {str(e)}")
            return []
    
    def log_analytics_event(self, user_id: str, event_type: str, event_data: Dict[str, Any]) -> str:
        """
        Log an analytics event
        
        Args:
            user_id: User ID
            event_type: Type of event
            event_data: Event data
            
        Returns:
            Event ID
        """
        try:
            conn = self.get_connection()
            if not conn:
                return ""
            
            cursor = conn.cursor()
            
            # Generate event ID
            event_id = str(uuid.uuid4())
            
            # Current timestamp
            timestamp = datetime.now().isoformat()
            
            # Convert event data to JSON string
            event_data_str = json.dumps(event_data)
            
            # Insert event
            cursor.execute(
                "INSERT INTO analytics (id, user_id, event_type, event_data, timestamp) VALUES (?, ?, ?, ?, ?)",
                (event_id, user_id, event_type, event_data_str, timestamp)
            )
            
            conn.commit()
            logger.debug(f"Logged analytics event: {event_type}")
            
            return event_id
            
        except Exception as e:
            logger.error(f"Error logging analytics event: {str(e)}")
            return ""
    
    def get_analytics_events(self, user_id: Optional[str] = None, event_type: Optional[str] = None, start_time: Optional[str] = None, end_time: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get analytics events
        
        Args:
            user_id: Filter by user ID (optional)
            event_type: Filter by event type (optional)
            start_time: Filter by start time (optional)
            end_time: Filter by end time (optional)
            limit: Maximum number of events to return
            
        Returns:
            List of event dictionaries
        """
        try:
            conn = self.get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            
            # Build query
            sql = "SELECT * FROM analytics WHERE 1=1"
            params = []
            
            if user_id:
                sql += " AND user_id = ?"
                params.append(user_id)
            
            if event_type:
                sql += " AND event_type = ?"
                params.append(event_type)
            
            if start_time:
                sql += " AND timestamp >= ?"
                params.append(start_time)
            
            if end_time:
                sql += " AND timestamp <= ?"
                params.append(end_time)
            
            sql += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            # Execute query
            cursor.execute(sql, tuple(params))
            events = cursor.fetchall()
            
            if not events:
                return []
            
            # Convert to dictionaries
            columns = [column[0] for column in cursor.description]
            event_dicts = []
            
            for event in events:
                event_dict = {columns[i]: event[i] for i in range(len(columns))}
                
                # Parse event data
                if "event_data" in event_dict:
                    try:
                        event_dict["event_data"] = json.loads(event_dict["event_data"])
                    except:
                        event_dict["event_data"] = {}
                
                event_dicts.append(event_dict)
            
            return event_dicts
            
        except Exception as e:
            logger.error(f"Error getting analytics events: {str(e)}")
            return []
    
    def close_connections(self) -> None:
        """Close all database connections"""
        try:
            for name, conn in self.connections.items():
                try:
                    conn.close()
                    logger.info(f"Closed database connection: {name}")
                except:
                    pass
            
            self.connections = {}
            
        except Exception as e:
            logger.error(f"Error closing connections: {str(e)}")

# Create a global instance
db_manager = DatabaseManager()

def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance"""
    return db_manager
