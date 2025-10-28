"""
Database Schema

This module defines the database schema for EVA using SQLAlchemy ORM.
"""

import os
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Boolean, Integer, Float, JSON, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

# Helper function to generate UUIDs
def generate_uuid():
    return str(uuid.uuid4())

# Association tables for many-to-many relationships
conversation_tag_association = Table(
    'conversation_tag_association',
    Base.metadata,
    Column('conversation_id', String(36), ForeignKey('conversations.id')),
    Column('tag_id', String(36), ForeignKey('tags.id'))
)

entity_tag_association = Table(
    'entity_tag_association',
    Base.metadata,
    Column('entity_id', String(36), ForeignKey('entities.id')),
    Column('tag_id', String(36), ForeignKey('tags.id'))
)

class User(Base):
    """User model"""
    __tablename__ = 'users'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(100), nullable=False, unique=True)
    email = Column(String(255), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow)
    preferences = Column(JSON, default={})
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user")
    analytics_events = relationship("AnalyticsEvent", back_populates="user")
    
    def __repr__(self):
        return f"<User(id='{self.id}', username='{self.username}')>"

class Conversation(Base):
    """Conversation model"""
    __tablename__ = 'conversations'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    title = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=conversation_tag_association, back_populates="conversations")
    
    def __repr__(self):
        return f"<Conversation(id='{self.id}', title='{self.title}')>"

class Message(Base):
    """Message model"""
    __tablename__ = 'messages'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey('conversations.id'), nullable=False)
    sender = Column(String(50), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON, default={})
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id='{self.id}', sender='{self.sender}')>"

class Entity(Base):
    """Entity model"""
    __tablename__ = 'entities'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    entity_type = Column(String(100), nullable=False)
    source = Column(String(100))
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    source_relationships = relationship("EntityRelationship", 
                                       foreign_keys="EntityRelationship.source_entity_id",
                                       back_populates="source_entity",
                                       cascade="all, delete-orphan")
    target_relationships = relationship("EntityRelationship", 
                                       foreign_keys="EntityRelationship.target_entity_id",
                                       back_populates="target_entity",
                                       cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=entity_tag_association, back_populates="entities")
    
    def __repr__(self):
        return f"<Entity(id='{self.id}', name='{self.name}', type='{self.entity_type}')>"

class EntityRelationship(Base):
    """Entity relationship model"""
    __tablename__ = 'entity_relationships'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    source_entity_id = Column(String(36), ForeignKey('entities.id'), nullable=False)
    target_entity_id = Column(String(36), ForeignKey('entities.id'), nullable=False)
    relationship_type = Column(String(100), nullable=False)
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    source_entity = relationship("Entity", foreign_keys=[source_entity_id], back_populates="source_relationships")
    target_entity = relationship("Entity", foreign_keys=[target_entity_id], back_populates="target_relationships")
    
    def __repr__(self):
        return f"<EntityRelationship(id='{self.id}', type='{self.relationship_type}')>"

class Tag(Base):
    """Tag model"""
    __tablename__ = 'tags'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversations = relationship("Conversation", secondary=conversation_tag_association, back_populates="tags")
    entities = relationship("Entity", secondary=entity_tag_association, back_populates="tags")
    
    def __repr__(self):
        return f"<Tag(id='{self.id}', name='{self.name}')>"

class AnalyticsEvent(Base):
    """Analytics event model"""
    __tablename__ = 'analytics'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    event_type = Column(String(100), nullable=False)
    event_data = Column(JSON, default={})
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="analytics_events")
    
    def __repr__(self):
        return f"<AnalyticsEvent(id='{self.id}', type='{self.event_type}')>"

class VectorEmbedding(Base):
    """Vector embedding model for semantic search"""
    __tablename__ = 'vector_embeddings'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    text_id = Column(String(36), nullable=False)  # ID of the associated text (message, entity, etc.)
    text_type = Column(String(50), nullable=False)  # Type of text (message, entity, etc.)
    embedding_type = Column(String(50), nullable=False)  # Type of embedding model used
    embedding = Column(JSON, nullable=False)  # Vector embedding as JSON array
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<VectorEmbedding(id='{self.id}', text_type='{self.text_type}', text_id='{self.text_id}')>"

class KnowledgeBase(Base):
    """Knowledge base model"""
    __tablename__ = 'knowledge_bases'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    documents = relationship("KnowledgeDocument", back_populates="knowledge_base", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<KnowledgeBase(id='{self.id}', name='{self.name}')>"

class KnowledgeDocument(Base):
    """Knowledge document model"""
    __tablename__ = 'knowledge_documents'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    knowledge_base_id = Column(String(36), ForeignKey('knowledge_bases.id'), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    document_type = Column(String(50), default="text")  # text, pdf, html, etc.
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<KnowledgeDocument(id='{self.id}', title='{self.title}')>"

class DocumentChunk(Base):
    """Document chunk model for retrieval augmented generation"""
    __tablename__ = 'document_chunks'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey('knowledge_documents.id'), nullable=False)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    metadata = Column(JSON, default={})
    embedding_id = Column(String(36), nullable=True)  # Reference to vector embedding
    
    # Relationships
    document = relationship("KnowledgeDocument", back_populates="chunks")
    
    def __repr__(self):
        return f"<DocumentChunk(id='{self.id}', document_id='{self.document_id}', index={self.chunk_index})>"

class UserSession(Base):
    """User session model"""
    __tablename__ = 'user_sessions'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    session_start = Column(DateTime, default=datetime.utcnow)
    session_end = Column(DateTime, nullable=True)
    device_info = Column(JSON, default={})
    metadata = Column(JSON, default={})
    
    def __repr__(self):
        return f"<UserSession(id='{self.id}', user_id='{self.user_id}')>"

class MLModel(Base):
    """Machine learning model metadata"""
    __tablename__ = 'ml_models'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False, unique=True)
    model_type = Column(String(50), nullable=False)  # classifier, regressor, etc.
    description = Column(Text)
    parameters = Column(JSON, default={})
    metrics = Column(JSON, default={})
    file_path = Column(String(255))  # Path to the model file
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<MLModel(id='{self.id}', name='{self.name}', type='{self.model_type}')>"
