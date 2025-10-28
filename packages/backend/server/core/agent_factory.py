"""
Factory for creating and initializing the Agent system.
"""

from loguru import logger
from typing import Optional

from .config import Config

# Heavy dependencies (LLM, RAG, tools) are imported lazily inside create_agent
# to avoid import-time failures in minimal environments (tests, static checks).


class AgentFactory:
    """Factory for creating fully configured Agent instances."""
    
    @staticmethod
    def create_agent(config: Optional[Config] = None):
        """
        Create a fully configured Agent instance.
        
        Args:
            config: Optional configuration (uses default if not provided)
            
        Returns:
            Configured Agent instance
        """
        if config is None:
            config = Config()
        
        logger.info("Initializing Agent system...")
        
        # Initialize LLM
        logger.info(f"Initializing LLM: {config.llm.provider} - {config.llm.model_name}")
        # Lazy import LLM client implementation. Support a 'stub' provider for offline/dev use.
        if config.llm.provider == "ollama":
            try:
                from .llm.ollama_client import OllamaClient
                llm = OllamaClient(
                    model_name=config.llm.model_name,
                    host=config.llm.host
                )
            except Exception as e:
                logger.warning(f"Failed to initialize real Ollama client, falling back to stub: {e}")
                from .llm.ollama_stub import OllamaStub
                llm = OllamaStub(model_name="stub-model")
        elif config.llm.provider in ("stub", "local-stub"):
            from .llm.ollama_stub import OllamaStub
            llm = OllamaStub(model_name=config.llm.model_name)
        else:
            raise ValueError(f"Unsupported LLM provider: {config.llm.provider}")
        
        # Initialize Vector Store
        logger.info("Initializing Vector Store and RAG Engine...")
        from .rag.vector_store import VectorStore
        from .rag.rag_engine import RAGEngine

        vector_store = VectorStore(
            collection_name=config.rag.collection_name,
            persist_directory=config.rag.persist_directory,
            embedding_model=config.rag.embedding_model
        )

        # Initialize RAG Engine
        rag_engine = RAGEngine(
            llm=llm,
            vector_store=vector_store,
            max_context_docs=config.rag.max_context_docs,
            similarity_threshold=config.rag.similarity_threshold
        )

        # Initialize Tool Registry
        logger.info("Initializing Tool Registry...")
        from .agent.tools import ToolRegistry, WebSearchTool, FileReadTool, CalculatorTool, CurrentTimeTool
        tool_registry = ToolRegistry()

        # Register built-in tools
        if config.agent.enable_tools:
            logger.info("Registering built-in tools...")
            tool_registry.register(WebSearchTool())
            tool_registry.register(FileReadTool())
            tool_registry.register(CalculatorTool())
            tool_registry.register(CurrentTimeTool())

        # Create Agent (lazy import)
        logger.info("Creating Agent...")
        from .agent.agent import Agent

        agent = Agent(
            llm=llm,
            rag_engine=rag_engine,
            tool_registry=tool_registry,
            max_iterations=config.agent.max_iterations
        )
        
        logger.info("Agent system initialized successfully!")
        return agent
    
    @staticmethod
    def create_minimal_agent(model_name: str = "llama3.2"):
        """
        Create a minimal agent with basic configuration.
        
        Args:
            model_name: Name of the Ollama model to use
            
        Returns:
            Basic Agent instance
        """
        config = Config()
        config.llm.model_name = model_name
        config.agent.enable_tools = False
        
        return AgentFactory.create_agent(config)

    @staticmethod
    def create_agent_no_rag(config: Optional[Config] = None):
        """Create an Agent instance without initializing RAG/VectorStore.

        Useful for demos and tests where embeddings/Chroma are not available.
        """
        if config is None:
            config = Config()

        logger.info("Initializing LLM for no-RAG agent")
        # Reuse LLM initialization logic
        if config.llm.provider == "ollama":
            try:
                from .llm.ollama_client import OllamaClient
                llm = OllamaClient(model_name=config.llm.model_name, host=config.llm.host)
            except Exception:
                from .llm.ollama_stub import OllamaStub
                llm = OllamaStub(model_name="stub-model")
        elif config.llm.provider in ("stub", "local-stub"):
            from .llm.ollama_stub import OllamaStub
            llm = OllamaStub(model_name=config.llm.model_name)
        else:
            raise ValueError(f"Unsupported LLM provider: {config.llm.provider}")

        # Minimal stub RAG engine
        class _DummyRAG:
            def retrieve_context(self, query):
                return []
            def add_to_memory(self, content, metadata=None):
                return None
            def get_memory_stats(self):
                return {}

        # Minimal ToolRegistry replacement
        class _DummyToolRegistry:
            def __init__(self):
                self.tools = []
            def get_tools_description(self):
                return "No tools available in demo mode."
            def list_tools(self):
                return []
            def get_tool(self, name):
                return None

        from .agent.agent import Agent

        agent = Agent(
            llm=llm,
            rag_engine=_DummyRAG(),
            tool_registry=_DummyToolRegistry(),
            max_iterations=config.agent.max_iterations
        )

        return agent


# Singleton instance
_agent_instance: Optional[object] = None


def get_agent(force_recreate: bool = False):
    """
    Get or create the global Agent instance.
    
    Args:
        force_recreate: Force recreation of the agent
        
    Returns:
        Agent instance
    """
    global _agent_instance
    
    if _agent_instance is None or force_recreate:
        _agent_instance = AgentFactory.create_agent()
    
    return _agent_instance
