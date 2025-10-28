"""
Base LLM interface for all language model providers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator
from dataclasses import dataclass


@dataclass
class Message:
    """Represents a chat message."""
    role: str  # 'system', 'user', 'assistant'
    content: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class LLMResponse:
    """Response from LLM."""
    content: str
    model: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseLLM(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name
        self.config = kwargs
    
    @abstractmethod
    def generate(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response from the LLM.
        
        Args:
            messages: List of conversation messages
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLMResponse object
        """
        pass
    
    @abstractmethod
    async def generate_stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Generate a streaming response from the LLM.
        
        Args:
            messages: List of conversation messages
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters
            
        Yields:
            Chunks of generated text
        """
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text.
        
        Args:
            text: Input text
            
        Returns:
            Number of tokens
        """
        pass
    
    def format_messages(self, messages: List[Message]) -> List[Dict[str, str]]:
        """
        Format messages for the LLM API.
        
        Args:
            messages: List of Message objects
            
        Returns:
            List of formatted message dictionaries
        """
        return [{"role": msg.role, "content": msg.content} for msg in messages]
