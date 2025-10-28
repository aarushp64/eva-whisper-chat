"""
Ollama LLM Client for local model inference.

Supports all Ollama models including:
- Llama 3.2, 3.1, 3
- Mistral, Mixtral
- Phi-3
- Gemma 2
- And more...
"""

import ollama
import asyncio
from typing import List, Optional, AsyncIterator, Dict, Any
from loguru import logger

from .base_llm import BaseLLM, Message, LLMResponse


class OllamaClient(BaseLLM):
    """Client for interacting with Ollama local LLM."""
    
    def __init__(
        self,
        model_name: str = "llama3.2",
        host: str = "http://localhost:11434",
        **kwargs
    ):
        """
        Initialize Ollama client.
        
        Args:
            model_name: Name of the Ollama model to use
            host: Ollama server URL
            **kwargs: Additional configuration
        """
        super().__init__(model_name, **kwargs)
        self.host = host
        self.client = ollama.Client(host=host)
        
        # Verify model is available
        self._ensure_model_available()
    
    def _ensure_model_available(self):
        """Check if model is available, pull if not."""
        try:
            models = self.client.list()
            model_names = [m['name'] for m in models.get('models', [])]
            
            if self.model_name not in model_names:
                logger.warning(f"Model {self.model_name} not found. Pulling...")
                self.client.pull(self.model_name)
                logger.info(f"Successfully pulled {self.model_name}")
        except Exception as e:
            logger.error(f"Error checking model availability: {e}")
            raise
    
    def generate(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response using Ollama.
        
        Args:
            messages: List of conversation messages
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Ollama parameters
            
        Returns:
            LLMResponse object
        """
        try:
            formatted_messages = self.format_messages(messages)
            
            options = {
                "temperature": temperature,
            }
            if max_tokens:
                options["num_predict"] = max_tokens
            
            # Merge with any additional options
            options.update(kwargs.get('options', {}))
            
            response = self.client.chat(
                model=self.model_name,
                messages=formatted_messages,
                options=options,
                stream=False
            )
            
            return LLMResponse(
                content=response['message']['content'],
                model=self.model_name,
                tokens_used=response.get('eval_count'),
                finish_reason=response.get('done_reason'),
                metadata={
                    'total_duration': response.get('total_duration'),
                    'load_duration': response.get('load_duration'),
                    'prompt_eval_count': response.get('prompt_eval_count'),
                }
            )
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    async def generate_stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Generate a streaming response using Ollama.
        
        Args:
            messages: List of conversation messages
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Ollama parameters
            
        Yields:
            Chunks of generated text
        """
        try:
            formatted_messages = self.format_messages(messages)
            
            options = {
                "temperature": temperature,
            }
            if max_tokens:
                options["num_predict"] = max_tokens
            
            options.update(kwargs.get('options', {}))
            
            stream = self.client.chat(
                model=self.model_name,
                messages=formatted_messages,
                options=options,
                stream=True
            )
            
            for chunk in stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    yield chunk['message']['content']
                    await asyncio.sleep(0)  # Allow other tasks to run
                    
        except Exception as e:
            logger.error(f"Error in streaming generation: {e}")
            raise
    
    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Note: This is an approximation. Ollama doesn't provide
        a built-in tokenizer, so we estimate ~4 chars per token.
        
        Args:
            text: Input text
            
        Returns:
            Estimated number of tokens
        """
        return len(text) // 4
    
    def get_embeddings(self, text: str) -> List[float]:
        """
        Generate embeddings for text using Ollama.
        
        Args:
            text: Input text
            
        Returns:
            List of embedding values
        """
        try:
            response = self.client.embeddings(
                model=self.model_name,
                prompt=text
            )
            return response['embedding']
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """
        List all available Ollama models.
        
        Returns:
            List of model information dictionaries
        """
        try:
            models = self.client.list()
            return models.get('models', [])
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
