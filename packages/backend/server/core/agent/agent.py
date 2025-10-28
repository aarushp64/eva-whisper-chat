"""
Main Agent class - The brain of Eva.

Combines LLM, RAG, and tool execution to create an intelligent agent
that can reason, remember, and take actions.
"""

from typing import List, Dict, Any, Optional, AsyncIterator
from loguru import logger
from datetime import datetime

from ..llm.base_llm import BaseLLM, Message
# Note: avoid importing heavy RAG module at import-time to keep imports lightweight
# The RAG engine type is only used for annotations; use a string annotation or
# lazy imports where necessary.
from .tools import ToolRegistry
from .executor import ToolExecutor


class Agent:
    """
    Intelligent agent that can:
    - Understand and respond to queries
    - Use tools to accomplish tasks
    - Remember and learn from interactions
    - Reason about complex problems
    """
    
    def __init__(
    self,
    llm: BaseLLM,
    rag_engine: Any,
    tool_registry: ToolRegistry,
    system_prompt: Optional[str] = None,
    max_iterations: int = 5
    ):
        """
        Initialize Agent.
        
        Args:
            llm: Language model instance
            rag_engine: RAG engine for context retrieval
            tool_registry: Registry of available tools
            system_prompt: Custom system prompt
            max_iterations: Maximum reasoning iterations
        """
        self.llm = llm
        self.rag_engine = rag_engine
        self.tool_registry = tool_registry
        self.tool_executor = ToolExecutor(tool_registry)
        self.max_iterations = max_iterations
        
        # Default system prompt
        self.system_prompt = system_prompt or self._get_default_system_prompt()
        
        logger.info("Agent initialized")
    
    def _get_default_system_prompt(self) -> str:
        """Get the default system prompt for the agent."""
        tools_desc = self.tool_registry.get_tools_description()
        
        return f"""You are Eva, an intelligent AI agent assistant. You can help users by:
1. Answering questions using your knowledge and memory
2. Using tools to accomplish tasks
3. Breaking down complex problems into steps
4. Learning from interactions to improve over time

{tools_desc}

When you need to use a tool, format it as:
TOOL_CALL: tool_name(param1="value1", param2="value2")

You can use multiple tools in sequence. After seeing tool results, provide a natural response to the user.

Be helpful, accurate, and conversational. If you're unsure, say so. Always explain your reasoning."""
    
    def process_query(
        self,
        query: str,
        conversation_history: Optional[List[Message]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user query with full agent capabilities.
        
        Args:
            query: User query
            conversation_history: Previous conversation messages
            user_id: Optional user ID for personalization
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            logger.info(f"Processing query: {query[:50]}...")
            
            # Initialize tracking
            iterations = 0
            tool_calls_made = []
            thinking_process = []
            
            # Get relevant context from RAG
            context_docs = self.rag_engine.retrieve_context(query)
            
            # Build initial messages
            messages = self._build_messages(
                query=query,
                conversation_history=conversation_history,
                context_docs=context_docs
            )
            
            # Agent reasoning loop
            while iterations < self.max_iterations:
                iterations += 1
                logger.info(f"Agent iteration {iterations}/{self.max_iterations}")
                
                # Generate response
                response = self.llm.generate(messages=messages, temperature=0.7)
                # Attach metadata if present
                entry = {
                    'iteration': iterations,
                    'thought': response.content
                }
                if hasattr(response, 'metadata') and response.metadata:
                    entry['metadata'] = response.metadata
                thinking_process.append(entry)
                
                # Check for tool calls
                tool_calls = self.tool_executor.parse_tool_calls_from_text(response.content)
                
                if not tool_calls:
                    # No tools needed, we have final answer
                    final_response = self._extract_final_response(response.content)
                    
                    # Store interaction in memory
                    self._store_interaction(
                        query=query,
                        response=final_response,
                        user_id=user_id,
                        tool_calls=tool_calls_made
                    )
                    
                    result = {
                        'response': final_response,
                        'tool_calls': tool_calls_made,
                        'iterations': iterations,
                        'thinking_process': thinking_process,
                        'context_used': context_docs,
                        'model': response.model
                    }
                    # include raw llm metadata if available
                    if hasattr(response, 'metadata') and response.metadata:
                        result['llm_metadata'] = response.metadata

                    return result
                
                # Execute tools
                logger.info(f"Executing {len(tool_calls)} tool(s)")
                tool_results = self.tool_executor.execute_tool_calls(tool_calls)
                tool_calls_made.extend(tool_results)
                
                # Add tool results to conversation
                tool_results_text = self.tool_executor.format_tool_results(tool_results)
                messages.append(Message(
                    role="assistant",
                    content=response.content
                ))
                messages.append(Message(
                    role="user",
                    content=f"Tool execution results:\n{tool_results_text}\n\nNow provide your final response to the user."
                ))
            
            # Max iterations reached
            logger.warning(f"Max iterations ({self.max_iterations}) reached")
            final_response = "I've been working on your request but need more time. Could you rephrase or break down your question?"
            
            return {
                'response': final_response,
                'tool_calls': tool_calls_made,
                'iterations': iterations,
                'thinking_process': thinking_process,
                'context_used': context_docs,
                'warning': 'Max iterations reached'
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            raise
    
    async def process_query_stream(
        self,
        query: str,
        conversation_history: Optional[List[Message]] = None,
        user_id: Optional[str] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Process query with streaming response.
        
        Args:
            query: User query
            conversation_history: Previous conversation messages
            user_id: Optional user ID
            
        Yields:
            Chunks of response data
        """
        try:
            logger.info(f"Processing streaming query: {query[:50]}...")
            
            # Get context
            context_docs = self.rag_engine.retrieve_context(query)
            
            # Yield context info
            yield {
                'type': 'context',
                'data': {'documents_found': len(context_docs)}
            }
            
            # Build messages
            messages = self._build_messages(
                query=query,
                conversation_history=conversation_history,
                context_docs=context_docs
            )
            
            # For streaming, we'll do a simpler approach without tool execution
            # (Tool execution requires waiting for full response)
            full_response = ""
            
            async for chunk in self.llm.generate_stream(messages=messages, temperature=0.7):
                full_response += chunk
                yield {
                    'type': 'content',
                    'data': {'chunk': chunk}
                }
            
            # Store interaction
            self._store_interaction(
                query=query,
                response=full_response,
                user_id=user_id
            )
            
            yield {
                'type': 'done',
                'data': {'complete': True}
            }
            
        except Exception as e:
            logger.error(f"Error in streaming query: {e}")
            yield {
                'type': 'error',
                'data': {'error': str(e)}
            }
    
    def _build_messages(
        self,
        query: str,
        conversation_history: Optional[List[Message]],
        context_docs: List[Dict[str, Any]]
    ) -> List[Message]:
        """Build message list for LLM."""
        messages = []
        
        # System prompt with context
        system_content = self.system_prompt
        if context_docs:
            context_str = self._format_context(context_docs)
            system_content += f"\n\nRelevant context from memory:\n{context_str}"
        
        messages.append(Message(role="system", content=system_content))
        
        # Add conversation history
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current query
        messages.append(Message(role="user", content=query))
        
        return messages
    
    def _format_context(self, context_docs: List[Dict[str, Any]]) -> str:
        """Format context documents."""
        if not context_docs:
            return ""
        
        formatted = []
        for i, doc in enumerate(context_docs[:3], 1):  # Limit to top 3
            formatted.append(f"[{i}] {doc['content']}")
        
        return "\n".join(formatted)
    
    def _extract_final_response(self, text: str) -> str:
        """Extract final response, removing tool call syntax."""
        # Remove any TOOL_CALL lines
        lines = text.split('\n')
        filtered_lines = [line for line in lines if not line.strip().startswith('TOOL_CALL:')]
        return '\n'.join(filtered_lines).strip()
    
    def _store_interaction(
        self,
        query: str,
        response: str,
        user_id: Optional[str] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None
    ):
        """Store interaction in memory for learning."""
        try:
            metadata = {
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id or 'anonymous',
                'type': 'conversation',
                'has_tools': bool(tool_calls)
            }
            
            # Store the interaction
            interaction_text = f"User: {query}\nAssistant: {response}"
            self.rag_engine.add_to_memory(
                content=interaction_text,
                metadata=metadata
            )
            
            logger.info("Interaction stored in memory")
        except Exception as e:
            logger.error(f"Error storing interaction: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics."""
        return {
            'model': self.llm.model_name,
            'tools_available': len(self.tool_registry.tools),
            'memory_stats': self.rag_engine.get_memory_stats(),
            'max_iterations': self.max_iterations
        }
