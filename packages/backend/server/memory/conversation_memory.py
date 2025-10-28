import json
from datetime import datetime
import numpy as np
import os
import pickle
import re

# langchain is an optional, heavier dependency. Provide lightweight fallbacks
# when it's not installed so the backend can run in demo/dev mode.
try:
    from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
    from langchain.embeddings import HuggingFaceEmbeddings
    from langchain.vectorstores import FAISS
    _LANGCHAIN_AVAILABLE = True
except Exception:
    _LANGCHAIN_AVAILABLE = False

    class _SimpleChatMemory:
        """Very small replacement for LangChain chat memory used only for
        buffering user/assistant messages when LangChain is unavailable."""
        def __init__(self):
            self.messages = []

        def add_user_message(self, text):
            self.messages.append({"sender": "user", "content": text, "timestamp": datetime.now().isoformat()})

        def add_ai_message(self, text):
            self.messages.append({"sender": "assistant", "content": text, "timestamp": datetime.now().isoformat()})

    class ConversationBufferMemory:
        def __init__(self, return_messages=False):
            self.return_messages = return_messages
            self.chat_memory = _SimpleChatMemory()

    class ConversationSummaryMemory(ConversationBufferMemory):
        def predict_new_summary(self, latest_message, current_summary):
            # Very small summarization fallback: append latest message excerpt
            excerpt = (latest_message[:200] + "...") if len(latest_message) > 200 else latest_message
            return (current_summary + " ") + "[summary excerpt] " + excerpt

    class HuggingFaceEmbeddings:
        def __init__(self, model_name=None):
            self.model_name = model_name

        def embed_documents(self, texts):
            # Return deterministic small vectors
            return [np.zeros(384).tolist() for _ in texts]

    class FAISS:
        @classmethod
        def from_texts(cls, texts, embeddings, metadatas=None):
            # Minimal in-memory store
            store = cls()
            store.docs = list(texts)
            return store

        def add_texts(self, texts, metadatas=None):
            if not hasattr(self, 'docs'):
                self.docs = []
            self.docs.extend(texts)

        def similarity_search_with_score(self, query, k=3):
            # naive fallback: return most recent docs with fake scores
            results = []
            if not hasattr(self, 'docs') or not self.docs:
                return []
            for i, d in enumerate(self.docs[:k]):
                class Doc:
                    def __init__(self, page_content):
                        self.page_content = page_content
                results.append((Doc(d), float(i + 1)))
            return results


class ConversationMemory:
    """Class to handle conversation memory and context tracking"""
    
    def __init__(self, user_id, chat_id=None, max_tokens=2000, memory_type="buffer"):
        self.user_id = user_id
        self.chat_id = chat_id
        self.max_tokens = max_tokens
        self.memory_type = memory_type
        self.messages = []
        self.summary = ""
        self.embeddings = None
        self.vector_store = None
        
        # Initialize memory based on type
        if memory_type == "buffer":
            self.memory = ConversationBufferMemory(return_messages=True)
        elif memory_type == "summary":
            self.memory = ConversationSummaryMemory(return_messages=True)
        else:
            self.memory = ConversationBufferMemory(return_messages=True)
        
        # Initialize embeddings for semantic search
        try:
            self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
        except Exception as e:
            print(f"Error initializing embeddings: {str(e)}")
    
    def add_message(self, message):
        """
        Add a message to the conversation memory
        
        Args:
            message (dict): Message object with sender, content, and timestamp
        """
        # Add message to the list
        self.messages.append(message)
        
        # Add to LangChain memory
        if message["sender"] == "user":
            self.memory.chat_memory.add_user_message(message["content"])
        else:
            self.memory.chat_memory.add_ai_message(message["content"])
        
        # Update vector store if embeddings are available
        if self.embeddings and message["content"].strip():
            self._update_vector_store(message)
    
    def _update_vector_store(self, message):
        """Update the vector store with a new message"""
        try:
            # Create vector store if it doesn't exist
            if self.vector_store is None:
                self.vector_store = FAISS.from_texts(
                    [message["content"]], 
                    self.embeddings, 
                    metadatas=[{"timestamp": message["timestamp"], "sender": message["sender"]}]
                )
            else:
                # Add the new message to the existing vector store
                self.vector_store.add_texts(
                    [message["content"]], 
                    metadatas=[{"timestamp": message["timestamp"], "sender": message["sender"]}]
                )
        except Exception as e:
            print(f"Error updating vector store: {str(e)}")
    
    def get_relevant_context(self, query, k=3):
        """
        Get the most relevant context for a query
        
        Args:
            query (str): The query to find relevant context for
            k (int): Number of relevant messages to retrieve
            
        Returns:
            list: List of relevant messages
        """
        if self.vector_store is None:
            # If no vector store, return the most recent messages
            return self.messages[-k:] if len(self.messages) >= k else self.messages
        
        try:
            # Search for relevant messages
            results = self.vector_store.similarity_search_with_score(query, k=k)
            
            # Extract messages and sort by relevance score
            relevant_messages = []
            for doc, score in results:
                # Find the original message
                for message in self.messages:
                    if message["content"] == doc.page_content:
                        relevant_messages.append({
                            **message,
                            "relevance_score": float(score)
                        })
                        break
            
            # Sort by relevance score (lower is better in FAISS)
            relevant_messages.sort(key=lambda x: x["relevance_score"])
            
            return relevant_messages
        except Exception as e:
            print(f"Error getting relevant context: {str(e)}")
            # Fallback to recent messages
            return self.messages[-k:] if len(self.messages) >= k else self.messages
    
    def get_conversation_summary(self):
        """
        Get a summary of the conversation
        
        Returns:
            str: Summary of the conversation
        """
        if self.memory_type == "summary":
            return self.memory.predict_new_summary(
                self.messages[-1]["content"],
                self.summary
            )
        else:
            # For buffer memory, create a simple summary
            if len(self.messages) == 0:
                return "No conversation history."
            
            user_messages = [m for m in self.messages if m["sender"] == "user"]
            assistant_messages = [m for m in self.messages if m["sender"] == "assistant"]
            
            summary = f"Conversation with {self.messages[0]['timestamp']}. "
            summary += f"User sent {len(user_messages)} messages. "
            summary += f"Assistant sent {len(assistant_messages)} messages."
            
            return summary
    
    def get_recent_messages(self, n=5):
        """
        Get the most recent messages
        
        Args:
            n (int): Number of recent messages to retrieve
            
        Returns:
            list: List of recent messages
        """
        return self.messages[-n:] if len(self.messages) >= n else self.messages
    
    def get_full_history(self):
        """
        Get the full conversation history
        
        Returns:
            list: List of all messages
        """
        return self.messages
    
    def clear(self):
        """Clear the conversation memory"""
        self.messages = []
        self.summary = ""
        self.memory.clear()
        self.vector_store = None
    
    def save(self, directory="memory"):
        """
        Save the conversation memory to disk
        
        Args:
            directory (str): Directory to save the memory to
        """
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        # Create a filename based on user_id and chat_id
        filename = f"{directory}/memory_{self.user_id}"
        if self.chat_id:
            filename += f"_{self.chat_id}"
        filename += ".pkl"
        
        # Save the messages and summary
        data = {
            "user_id": self.user_id,
            "chat_id": self.chat_id,
            "messages": self.messages,
            "summary": self.summary,
            "memory_type": self.memory_type,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(filename, "wb") as f:
            pickle.dump(data, f)
        
        # Save vector store if it exists
        if self.vector_store:
            vector_filename = f"{directory}/vectors_{self.user_id}"
            if self.chat_id:
                vector_filename += f"_{self.chat_id}"
            
            self.vector_store.save_local(vector_filename)
    
    @classmethod
    def load(cls, user_id, chat_id=None, directory="memory"):
        """
        Load conversation memory from disk
        
        Args:
            user_id (str): User ID
            chat_id (str): Chat ID
            directory (str): Directory to load the memory from
            
        Returns:
            ConversationMemory: Loaded conversation memory
        """
        # Create filename based on user_id and chat_id
        filename = f"{directory}/memory_{user_id}"
        if chat_id:
            filename += f"_{chat_id}"
        filename += ".pkl"
        
        # Check if file exists
        if not os.path.exists(filename):
            return cls(user_id, chat_id)
        
        try:
            # Load data
            with open(filename, "rb") as f:
                data = pickle.load(f)
            
            # Create a new instance
            memory = cls(user_id, chat_id, memory_type=data["memory_type"])
            memory.messages = data["messages"]
            memory.summary = data["summary"]
            
            # Reload messages into LangChain memory
            for message in memory.messages:
                if message["sender"] == "user":
                    memory.memory.chat_memory.add_user_message(message["content"])
                else:
                    memory.memory.chat_memory.add_ai_message(message["content"])
            
            # Load vector store if it exists
            vector_filename = f"{directory}/vectors_{user_id}"
            if chat_id:
                vector_filename += f"_{chat_id}"
            
            if os.path.exists(vector_filename):
                try:
                    memory.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
                    memory.vector_store = FAISS.load_local(vector_filename, memory.embeddings)
                except Exception as e:
                    print(f"Error loading vector store: {str(e)}")
            
            return memory
        except Exception as e:
            print(f"Error loading memory: {str(e)}")
            return cls(user_id, chat_id)

class ThreadedMemory:
    """Class to handle threaded conversations with multiple topics"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.threads = {}  # Map of thread_id -> ConversationMemory
        self.active_thread_id = None
    
    def create_thread(self, thread_id=None, title=None):
        """
        Create a new conversation thread
        
        Args:
            thread_id (str): Thread ID (optional, will be generated if not provided)
            title (str): Thread title
            
        Returns:
            str: Thread ID
        """
        # Generate thread_id if not provided
        if thread_id is None:
            thread_id = f"thread_{len(self.threads) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create a new conversation memory
        self.threads[thread_id] = {
            "memory": ConversationMemory(self.user_id, thread_id),
            "title": title or f"Thread {len(self.threads) + 1}",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Set as active thread if this is the first thread
        if self.active_thread_id is None:
            self.active_thread_id = thread_id
        
        return thread_id
    
    def get_thread(self, thread_id=None):
        """
        Get a conversation thread
        
        Args:
            thread_id (str): Thread ID (if None, returns the active thread)
            
        Returns:
            dict: Thread information including memory
        """
        if thread_id is None:
            thread_id = self.active_thread_id
        
        if thread_id not in self.threads:
            return None
        
        return self.threads[thread_id]
    
    def set_active_thread(self, thread_id):
        """
        Set the active conversation thread
        
        Args:
            thread_id (str): Thread ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        if thread_id not in self.threads:
            return False
        
        self.active_thread_id = thread_id
        return True
    
    def add_message(self, message, thread_id=None):
        """
        Add a message to a conversation thread
        
        Args:
            message (dict): Message object with sender, content, and timestamp
            thread_id (str): Thread ID (if None, adds to the active thread)
        """
        if thread_id is None:
            thread_id = self.active_thread_id
        
        # Create thread if it doesn't exist
        if thread_id not in self.threads:
            thread_id = self.create_thread(thread_id)
        
        # Add message to the thread
        self.threads[thread_id]["memory"].add_message(message)
        
        # Update thread timestamp
        self.threads[thread_id]["updated_at"] = datetime.now().isoformat()
    
    def get_thread_list(self):
        """
        Get a list of all conversation threads
        
        Returns:
            list: List of thread information
        """
        return [
            {
                "thread_id": thread_id,
                "title": thread["title"],
                "created_at": thread["created_at"],
                "updated_at": thread["updated_at"],
                "message_count": len(thread["memory"].messages),
                "is_active": thread_id == self.active_thread_id
            }
            for thread_id, thread in self.threads.items()
        ]
    
    def delete_thread(self, thread_id):
        """
        Delete a conversation thread
        
        Args:
            thread_id (str): Thread ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        if thread_id not in self.threads:
            return False
        
        # Delete the thread
        del self.threads[thread_id]
        
        # Update active thread if needed
        if thread_id == self.active_thread_id:
            if self.threads:
                self.active_thread_id = next(iter(self.threads))
            else:
                self.active_thread_id = None
        
        return True
    
    def save(self, directory="memory"):
        """
        Save all conversation threads to disk
        
        Args:
            directory (str): Directory to save the memory to
        """
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        # Save thread metadata
        metadata = {
            "user_id": self.user_id,
            "active_thread_id": self.active_thread_id,
            "threads": {
                thread_id: {
                    "title": thread["title"],
                    "created_at": thread["created_at"],
                    "updated_at": thread["updated_at"]
                }
                for thread_id, thread in self.threads.items()
            }
        }
        
        metadata_filename = f"{directory}/threads_{self.user_id}.json"
        with open(metadata_filename, "w") as f:
            json.dump(metadata, f)
        
        # Save each thread's memory
        for thread_id, thread in self.threads.items():
            thread["memory"].save(directory)
    
    @classmethod
    def load(cls, user_id, directory="memory"):
        """
        Load conversation threads from disk
        
        Args:
            user_id (str): User ID
            directory (str): Directory to load the memory from
            
        Returns:
            ThreadedMemory: Loaded threaded memory
        """
        # Create a new instance
        threaded_memory = cls(user_id)
        
        # Check if metadata file exists
        metadata_filename = f"{directory}/threads_{user_id}.json"
        if not os.path.exists(metadata_filename):
            return threaded_memory
        
        try:
            # Load metadata
            with open(metadata_filename, "r") as f:
                metadata = json.load(f)
            
            # Set active thread
            threaded_memory.active_thread_id = metadata.get("active_thread_id")
            
            # Load each thread
            for thread_id, thread_metadata in metadata.get("threads", {}).items():
                # Load thread memory
                memory = ConversationMemory.load(user_id, thread_id, directory)
                
                # Add thread to threaded memory
                threaded_memory.threads[thread_id] = {
                    "memory": memory,
                    "title": thread_metadata.get("title", f"Thread {thread_id}"),
                    "created_at": thread_metadata.get("created_at", datetime.now().isoformat()),
                    "updated_at": thread_metadata.get("updated_at", datetime.now().isoformat())
                }
            
            return threaded_memory
        except Exception as e:
            print(f"Error loading threaded memory: {str(e)}")
            return cls(user_id)
